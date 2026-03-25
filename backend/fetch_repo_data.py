import sys
import json
import logging
import os
from datetime import datetime
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from github import Github, RateLimitExceededException
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
load_dotenv()

def extract_repo_name(url):
    clean_url = url.rstrip('/')
    parts = clean_url.split('/')
    return f"{parts[-2]}/{parts[-1]}" if len(parts) >= 2 else url

def categorize_commit(message):
    msg = message.lower()
    if any(x in msg for x in ['feat', 'add', 'impl']): return 'feature'
    if any(x in msg for x in ['fix', 'bug', 'patch']): return 'fix'
    if any(x in msg for x in ['refactor', 'clean', 'style']): return 'refactor'
    if any(x in msg for x in ['doc', 'readme']): return 'docs'
    return 'other'

def fetch_commit_details(commit):
    try:
        files_added = 0
        files_modified = 0
        files_deleted = 0
        focus_files = []
        lines_plus = 0
        lines_minus = 0
        
        # This requires an individual API call and triggers rate limits easily
        try:
            for f in commit.files:
                if f.status == 'added': 
                    files_added += 1
                elif f.status in ['removed', 'deleted']: 
                    files_deleted += 1
                else: 
                    files_modified += 1
                    
                if len(focus_files) < 5:
                    focus_files.append(f.filename)

            lines_plus = commit.stats.additions
            lines_minus = commit.stats.deletions
        except Exception as api_err:
            # If rate limited, just skip the deep file stats but keep the core commit!
            pass

        return {
            "timestamp": commit.commit.author.date.isoformat(),
            "date": commit.commit.author.date.strftime('%Y-%m-%d'),
            "category": categorize_commit(commit.commit.message),
            "contributor": commit.commit.author.name or "Unknown",
            "impact": {
                "files_changed_count": files_modified,
                "files_added_count": files_added,
                "files_deleted_count": files_deleted,
                "lines_plus": lines_plus,
                "lines_minus": lines_minus
            },
            "message": commit.commit.message.split('\n')[0],
            "focus_files": focus_files
        }
    except Exception as e:
        logging.error(f"Failed parsing commit: {e}")
        return None

def main(repo_url, output_dir):
    repo_name_str = extract_repo_name(repo_url)
    os.makedirs(output_dir, exist_ok=True)
    token = os.environ.get("GITHUB_TOKEN")
    gh = Github(token) if token else Github()
        
    try:
        repo = gh.get_repo(repo_name_str)
        
        # Fetching up to 100 commits based on user request
        commits = list(repo.get_commits()[:100])
        logging.info(f"Total commits found to process: {len(commits)}")
        
        timeline = []
        category_counts = Counter()
        heatmap = {} # contributor -> { date -> count }
        global_timeline = Counter() # date -> count
        
        with ThreadPoolExecutor(max_workers=10) as exe:
            futures = [exe.submit(fetch_commit_details, c) for c in commits]
            for i, f in enumerate(as_completed(futures)):
                res = f.result()
                if res:
                    timeline.append(res)
                    category_counts[res['category']] += 1
                    
                    contrib = res['contributor']
                    date_str = res['date']
                    if contrib not in heatmap:
                        heatmap[contrib] = Counter()
                    heatmap[contrib][date_str] += 1
                    global_timeline[date_str] += 1
                    
                if (i + 1) % 25 == 0:
                    logging.info(f"Processed {i + 1}/{len(commits)} commits...")
        
        timeline.sort(key=lambda x: x['timestamp'])
        
        # Clean up temporary date fields
        for t in timeline:
            if 'date' in t:
                del t['date']
                
        # Fetching all top contributors instead of just 15
        contribs = [{"name": c.login, "commits": c.contributions} for c in repo.get_contributors()]
        
        heatmap_formatted = {k: dict(v) for k, v in heatmap.items()}
        timeline_formatted = dict(sorted(global_timeline.items()))
        
        open_prs = 0
        closed_prs = 0
        try:
            for pr in repo.get_pulls(state='all')[:50]:
                if pr.state == 'open': open_prs += 1
                else: closed_prs += 1
        except Exception: pass
            
        try: topics = repo.get_topics()
        except: topics = []
            
        try:
            created_at_iso = repo.created_at.isoformat()
            if repo.created_at.tzinfo is None:
                import datetime as dt_utils
                aware_dt = repo.created_at.replace(tzinfo=dt_utils.timezone.utc)
                age_days = (datetime.now(dt_utils.timezone.utc) - aware_dt).days
            else:
                age_days = (datetime.now(repo.created_at.tzinfo) - repo.created_at).days
        except:
            created_at_iso = ""
            age_days = 0
            
        # Natively lazy loaded PyGithub properties which might throw RateLimit 
        try: forks = getattr(repo, 'forks_count', 0)
        except: forks = 0
        try: issues = getattr(repo, 'open_issues_count', 0)
        except: issues = 0
        try: watchers = getattr(repo, 'subscribers_count', 0)
        except: watchers = 0

        data = {
            "repo_name": repo.full_name,
            "description": repo.description or "",
            "total_commits_fetched": len(timeline),
            "analytics": {"commit_categories": dict(category_counts)},
            "top_contributors": contribs,
            "commit_frequency_timeline": timeline_formatted,
            "contributor_heatmap": heatmap_formatted,
            "timeline_segments": timeline,
            "global_stats": {
                "languages": dict(Counter(repo.get_languages()).most_common(6)),
                "top_contributors": contribs,
                "stars": getattr(repo, 'stargazers_count', 0),
                "forks": forks,
                "issues": issues,
                "watchers": watchers,
                "created_at": created_at_iso,
                "age_days": age_days,
                "topics": topics,
                "prs": {"open": open_prs, "closed": closed_prs}
            }
        }
        
        with open(os.path.join(output_dir, "repo_data.json"), "w") as f:
            json.dump(data, f, indent=2)
        logging.info("Successfully generated data JSON.")
        
        # Construct and save a line graph as requested
        try:
            import matplotlib.pyplot as plt
            dates = list(timeline_formatted.keys())
            counts = list(timeline_formatted.values())
            
            plt.figure(figsize=(10, 5))
            plt.plot(dates, counts, marker='o', linestyle='-', color='#58a6ff')
            plt.title(f"Commit Timeline ({repo.full_name})")
            plt.xlabel("Days")
            plt.ylabel("Number of Commits")
            plt.xticks(rotation=45, ha='right')
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()
            
            graph_path = os.path.join(output_dir, "commit_timeline_graph.png")
            plt.savefig(graph_path)
            logging.info(f"Successfully generated line graph at {graph_path}")
        except ImportError:
            logging.warning("matplotlib not found. Line graph was not generated. Install with 'pip install matplotlib'.")
            
    except RateLimitExceededException:
        logging.error("GitHub API Rate Limit Exceeded. You may need to provide a GITHUB_TOKEN or wait until your limit resets.")
    except Exception as e:
        logging.error(f"Fetch failed: {e}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
