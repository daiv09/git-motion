import os
import json
import numpy as np
from manim import *
import themes
import datetime

class ProjectBiography(Scene):
    def construct(self):
        # 1. Load Data
        json_path = os.environ.get("REPO_JSON_PATH", "repo_data.json")
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
        except Exception as e:
            self.play(Write(Text(f"Error loading {json_path}", color=RED, font_size=24)))
            return

        # 2. Setup Theme
        t = themes.get_theme(os.environ.get("THEME", "github_dark"))
        self.camera.background_color = t["bg"]

        repo_name = data.get("repo_name", "Repository")
        description = data.get("description", "")
        if not description:
             description = "A GitHub Repository"
             
        global_stats = data.get("global_stats", {})
        stars = global_stats.get("stars", 0)
        langs_dict = global_stats.get("languages", {})
        top_lang = list(langs_dict.keys())[0] if langs_dict else "Various"
        
        timeline = data.get("timeline_segments", [])
        categories = data.get("analytics", {}).get("commit_categories", {})
        contributors = data.get("top_contributors", [])
        if not contributors:
            contributors = global_stats.get("top_contributors", [])

        # --- SCENE 1: Intro ---
        title = Text(repo_name, font_size=42, weight=BOLD).set_color(t["primary"])

        desc_text = Text(
            description[:60] + ("..." if len(description) > 60 else ""),
            font_size=24, color=t["text"], slant=ITALIC
        )

        stats_text = Text(
            f"★ {stars} Stars   •   {top_lang}   •   {len(timeline)} Commits", 
            font_size=20, color=t["sub"]
        )

        intro_group = VGroup(title, desc_text, stats_text).arrange(DOWN, buff=0.5)

        self.play(FadeIn(title, shift=UP), run_time=1)
        self.play(Write(desc_text), run_time=1)
        self.play(FadeIn(stats_text, shift=UP), run_time=1)
        self.wait(1.5)
        self.play(FadeOut(intro_group, shift=UP))

        # --- SCENE 2: Pulse Dashboard ---
        forks = global_stats.get("forks", 0)
        issues = global_stats.get("issues", 0)
        watchers = global_stats.get("watchers", 0)
        
        pulse_title = Text("Repository Pulse", font_size=36, color=t["text"]).to_edge(UP, buff=0.5)
        self.play(FadeIn(pulse_title, shift=DOWN))
        
        def make_counter(label_str, target_val, color):
            tracker = ValueTracker(0)
            num_text = Text("0", font_size=48, color=color, weight=BOLD)
            
            def update_num(m):
                val = int(tracker.get_value())
                new_text = Text(str(val), font_size=48, color=color, weight=BOLD)
                new_text.move_to(m.get_center())
                m.become(new_text)
                
            num_text.add_updater(update_num)
            
            lbl = Text(label_str, font_size=20, color=t["text"]).next_to(num_text, DOWN, buff=0.3)
            v_g = VGroup(num_text, lbl).arrange(DOWN, buff=0.3)
            return v_g, tracker
            
        cg1, tr1 = make_counter("Forks", forks, t["accent"])
        cg2, tr2 = make_counter("Issues", issues, t.get("red", RED))
        cg3, tr3 = make_counter("Watchers", watchers, t.get("green", GREEN))
        
        dash_group = VGroup(cg1, cg2, cg3).arrange(RIGHT, buff=2).move_to(ORIGIN)
        # Fix height differences manually by aligning bottoms of labels
        cg1[1].align_to(cg2[1], DOWN)
        cg3[1].align_to(cg2[1], DOWN)
        cg1[0].next_to(cg1[1], UP, buff=0.3)
        cg3[0].next_to(cg3[1], UP, buff=0.3)
        
        self.play(FadeIn(dash_group, shift=UP))
        
        self.play(
            tr1.animate.set_value(forks),
            tr2.animate.set_value(issues),
            tr3.animate.set_value(watchers),
            run_time=2, rate_func=smooth
        )
        self.wait(1.5)
        self.play(FadeOut(dash_group), FadeOut(pulse_title))

        # --- SCENE 3: Animated Pie Chart (Improved) ---
        if langs_dict:
            lang_title = Text("Language Distribution", font_size=36, color=t["text"]).to_edge(UP, buff=0.5)
            self.play(FadeIn(lang_title, shift=DOWN))
            
            total_bytes = sum(langs_dict.values())
            if total_bytes > 0:
                chart_radius = 2.2
                # Using a more vibrant, distinct color palette
                colors = [t["primary"], t.get("green", "#3fb950"), t["accent"], 
                        t.get("red", "#f85149"), t.get("sub", "#8b949e")]
                
                current_angle = 90 * DEGREES 
                # Only take languages that actually have a visible percentage (>1%) to avoid clutter
                sorted_langs = [item for item in sorted(langs_dict.items(), key=lambda x: x[1], reverse=True) if (item[1]/total_bytes) > 0.01][:5]
                
                slices = VGroup()
                labels_with_lines = VGroup()

                for i, (lang, bytes_count) in enumerate(sorted_langs):
                    pct = bytes_count / total_bytes
                    sweep_angle = pct * TAU # Use TAU for full circle
                    color = colors[i % len(colors)]
                    
                    # Create sector centered at ORIGIN
                    sector = Sector(
                        radius=chart_radius,
                        start_angle=current_angle,
                        angle=-sweep_angle, # Clockwise
                        color=color,
                        fill_opacity=0.9,
                        stroke_width=3,
                        stroke_color=t["bg"] # This creates the "gap" look between slices
                    )
                    
                    mid_angle = current_angle - (sweep_angle / 2)
                    direction_vector = np.array([np.cos(mid_angle), np.sin(mid_angle), 0])
                    
                    # Subtle "exploded" effect: shift each slice slightly outward
                    sector.shift(direction_vector * 0.1)
                    slices.add(sector)
                    
                    # Refined Labeling
                    line_start = direction_vector * (chart_radius + 0.15)
                    line_end = direction_vector * (chart_radius + 0.6)
                    callout = Line(line_start, line_end, stroke_width=2, color=t["sub"])
                    
                    lbl = Text(f"{lang}: {pct:.1%}", font_size=20, color=t["text"])
                    
                    # Avoid label overlap by checking X-direction
                    if direction_vector[0] >= 0:
                        lbl.next_to(callout, RIGHT, buff=0.2)
                    else:
                        lbl.next_to(callout, LEFT, buff=0.2)
                        
                    labels_with_lines.add(VGroup(callout, lbl))
                    current_angle -= sweep_angle
                
                # Group and center everything
                main_chart = VGroup(slices, labels_with_lines).center().shift(DOWN * 0.3)
                
                # Animation: Scale in each slice with a bounce
                self.play(
                    LaggedStart(
                        *[DrawBorderThenFill(s) for s in slices],
                        lag_ratio=0.15,
                        run_time=2
                    )
                )
                
                self.play(
                    LaggedStart(
                        *[Create(l[0]) for l in labels_with_lines], # Draw lines
                        *[Write(l[1]) for l in labels_with_lines],  # Write text
                        lag_ratio=0.1,
                        run_time=1.5
                    )
                )

                self.wait(2.5)
                self.play(FadeOut(main_chart, scale=0.8), FadeOut(lang_title, shift=UP))

        # --- SCENE 4: Repository Age & Lifespan (Premium Version) ---
        age_days = global_stats.get("age_days", 0)
        created_at_iso = global_stats.get("created_at", "")

        if age_days > 0 and created_at_iso:
            age_title = Text("Repository Lifespan", font_size=36, color=t["text"]).to_edge(UP, buff=0.5)
            self.play(FadeIn(age_title, shift=DOWN))
            
            # 1. Date Calculations
            years = age_days // 365
            months = (age_days % 365) // 30
            age_str = f"{years} Years, {months} Months" if years > 0 else f"{months} Months"
            
            created_dt = datetime.datetime.fromisoformat(created_at_iso.replace("Z", "+00:00"))
            create_str = created_dt.strftime("%b %Y")
            now_str = datetime.datetime.now().strftime("%b %Y")
            
            # 2. Geometry Setup
            line_w = 9
            full_line = Line(LEFT * (line_w/2), RIGHT * (line_w/2), color=t["secondary"], stroke_width=4, stroke_opacity=0.3)
            progress_line = Line(LEFT * (line_w/2), RIGHT * (line_w/2), color=t["primary"], stroke_width=8)
            
            dot_start = Dot(full_line.get_start(), color=t["primary"], radius=0.18)
            # A glowing dot for the 'present day'
            dot_end = Dot(full_line.get_end(), color=t["primary"], radius=0.12)
            dot_end.add(dot_end.copy().set_stroke(width=10, opacity=0.3).scale(1.5)) 
            
            lbl_start = Text(create_str, font_size=20, color=t["text"]).next_to(dot_start, DOWN, buff=0.4)
            lbl_end = Text(now_str, font_size=20, color=t["text"]).next_to(dot_end, DOWN, buff=0.4)
            
            # Age Text: Large and centered
            age_display = Text(age_str, font_size=48, weight=BOLD, color=t["accent"]).shift(UP * 1.2)
            since_text = Text("Active since", font_size=20, color=t["sub"]).next_to(age_display, UP, buff=0.2)
            
            # 3. Animations
            # Show initial state
            self.play(
                FadeIn(full_line),
                FadeIn(dot_start, scale=0.5),
                Write(lbl_start),
                run_time=0.8
            )
            
            # Draw the progress line and pop in the Age Text
            self.play(
                Create(progress_line),
                FadeIn(since_text, shift=UP),
                Write(age_display),
                UpdateFromAlphaFunc(dot_end, lambda m, a: m.move_to(progress_line.point_from_proportion(a))),
                run_time=2.5,
                rate_func=slow_into
            )
            
            # Highlight the final date
            self.play(FadeIn(lbl_end, shift=UP), dot_end.animate.scale(1.2))
            
            self.wait(2.5)
            
            # Outro
            self.play(
                FadeOut(VGroup(full_line, progress_line, dot_start, dot_end, lbl_start, lbl_end, age_display, since_text, age_title), shift=DOWN),
                run_time=1
            )

        # --- SCENE 5: Repository Topics (Structured Grid) ---
        topics = global_stats.get("topics", [])
        if topics:
            topics = topics[:12] # Limit to 12 for a clean grid
            cloud_title = Text("Repository Topics", font_size=40, weight=BOLD, color=t["text"]).to_edge(UP, buff=0.7)
            self.play(FadeIn(cloud_title, shift=DOWN))
            
            bubbles = VGroup()
            for topic in topics:
                # badge text
                t_lbl = Text(topic.lower(), font_size=16, color=t["primary"], weight=SEMIBOLD)
                
                # badge background (Glassmorphism look: subtle border, low opacity fill)
                bg = RoundedRectangle(
                    corner_radius=0.15, 
                    width=max(t_lbl.width + 0.6, 2.0), # Ensure minimum width for structure
                    height=0.7, 
                    fill_color=t["primary"], 
                    fill_opacity=0.1, 
                    stroke_color=t["primary"], 
                    stroke_width=1.5
                )
                
                badge = VGroup(bg, t_lbl)
                bubbles.add(badge)
                
            # Arrange in a clean grid (3 or 4 columns depending on count)
            cols = 3 if len(topics) <= 9 else 4
            bubbles.arrange_in_grid(cols=cols, buff=0.4).move_to(ORIGIN).shift(DOWN * 0.3)
            
            # Animation: Staggered FadeIn with subtle scale
            self.play(
                LaggedStart(
                    *[FadeIn(b, scale=0.9, shift=UP*0.2) for b in bubbles],
                    lag_ratio=0.08,
                    run_time=2
                )
            )
            
            self.wait(2.5)
            
            # Unified Outro
            self.play(
                FadeOut(bubbles, shift=DOWN * 0.5),
                FadeOut(cloud_title, shift=UP * 0.5),
                run_time=1
            )

        # --- SCENE 6: Activity Feed (Split-Card Design) ---
        if timeline:
            added_tracker = ValueTracker(0)
            deleted_tracker = ValueTracker(0)

            # Arrange counters with ample buffer to prevent overlap as numbers grow
            # counter_group = VGroup(c_added_grp, c_deleted_grp).arrange(RIGHT, buff=1.0).to_edge(UP, buff=0.8)
            
            # self.play(FadeIn(counter_group, shift=DOWN))

            individual_limit = 10
            recent_commits = timeline[-individual_limit:]

            # Fast-forward tally for older commits
            older_commits = timeline[:-individual_limit]
            if older_commits:
                pre_plus = sum(c.get("impact", {}).get("lines_plus", 0) for c in older_commits)
                pre_minus = sum(c.get("impact", {}).get("lines_minus", 0) for c in older_commits)
                self.play(added_tracker.animate.set_value(pre_plus), deleted_tracker.animate.set_value(pre_minus), run_time=0.8)

            # 2. Iterative Card Animation
            for i, commit in enumerate(recent_commits):
                # Card Base
                card_w, card_h = 9, 2.0
                card_bg = RoundedRectangle(corner_radius=0.15, width=card_w, height=card_h, 
                                        fill_color=t["secondary"], fill_opacity=1, 
                                        stroke_color=t["primary"], stroke_width=1.5)
                
                # Vertical Separator (Dash style)
                sep = Line(UP*0.7, DOWN*0.7, color=t["primary"], stroke_opacity=0.3).shift(RIGHT * 2.2)

                # Left Side: Message & Author
                msg_text = commit.get("message", "Commit")[:55] + ("..." if len(commit.get("message", "")) > 55 else "")
                msg = Text(f"\"{msg_text}\"", font_size=18, color=t["text"], weight=MEDIUM).align_to(card_bg, LEFT).shift(RIGHT * 0.5 + UP * 0.2)
                auth = Text(f"by {commit.get('contributor', 'user')}", font_size=14, color=t["accent"], slant=ITALIC).next_to(msg, DOWN, aligned_edge=LEFT, buff=0.15)
                
                # Right Side: Impact Badge
                p = commit.get("impact", {}).get("lines_plus", 0)
                m = commit.get("impact", {}).get("lines_minus", 0)
                p_text = Text(f"+{p}", color=t.get("green", "#3fb950"), font_size=18, weight=BOLD)
                m_text = Text(f"-{m}", color=t.get("red", "#f85149"), font_size=18, weight=BOLD)
                impact_grp = VGroup(p_text, m_text).arrange(DOWN, buff=0.2).next_to(sep, RIGHT, buff=0.5)

                v_group = VGroup(card_bg, sep, msg, auth, impact_grp).move_to(DOWN * 5)

                # Animation Sequence
                self.play(
                    v_group.animate.move_to(ORIGIN),
                    added_tracker.animate.set_value(added_tracker.get_value() + p),
                    deleted_tracker.animate.set_value(deleted_tracker.get_value() + m),
                    # Pulse the specific tracker being updated
                    # c_added_grp.animate.scale(1.1) if p > 0 else Wait(),
                    # c_deleted_grp.animate.scale(1.1) if m > 0 else Wait(),
                    run_time=0.45,
                    rate_func=smooth
                )
                
                # self.play(c_added_grp.animate.scale(1/1.1), c_deleted_grp.animate.scale(1/1.1), run_time=0.1)
                # self.wait(0.8)
                
                # Smooth Exit: Slides slightly left and fades
                self.play(
                    v_group.animate.shift(LEFT * 2).set_opacity(0),
                    run_time=0.4,
                    rate_func=linear
                )

            # self.play(FadeOut(counter_group))

        # --- SCENE 7: Pull Request Health (Dashboard Style) ---
        prs = global_stats.get("prs", {})
        open_prs = prs.get("open", 0)
        closed_prs = prs.get("closed", 0)
        total_prs = open_prs + closed_prs

        if total_prs > 0:
            pr_title = Text("Pull Request Health", font_size=36, color=t["text"]).to_edge(UP, buff=0.5)
            self.play(FadeIn(pr_title, shift=DOWN))
            
            # 1. Setup Dimensions & Ratios
            bar_w, bar_h = 9, 0.6
            closed_ratio = closed_prs / total_prs
            
            # Background "Track"
            track = RoundedRectangle(
                corner_radius=0.1, width=bar_w, height=bar_h, 
                fill_color=t["secondary"], fill_opacity=0.3, stroke_width=0
            ).move_to(ORIGIN)

            # Merged/Closed Bar
            w_c = max(bar_w * closed_ratio, 0.1)
            closed_rect = RoundedRectangle(
                corner_radius=0.1, width=w_c, height=bar_h,
                fill_color=t.get("green", "#3fb950"), fill_opacity=0.9, stroke_width=0
            )
            
            # Open Bar (positioned to the right of closed)
            w_o = max(bar_w * (1 - closed_ratio), 0.1)
            open_rect = RoundedRectangle(
                corner_radius=0.1, width=w_o, height=bar_h,
                fill_color=t.get("red", "#f85149"), fill_opacity=0.9, stroke_width=0
            )
            
            # Group them so we can anchor the movement
            bar_group = VGroup(closed_rect, open_rect).arrange(RIGHT, buff=0.05).move_to(ORIGIN)

            # 2. Labels & Percentages
            pct_closed = Text(f"{closed_ratio:.0%}", font_size=24, weight=BOLD, color=t.get("green", "#3fb950"))
            lbl_closed = Text("Merged", font_size=16, color=t["sub"]).next_to(pct_closed, DOWN, buff=0.1)
            merged_grp = VGroup(pct_closed, lbl_closed).next_to(closed_rect, UP, buff=0.4).align_to(closed_rect, LEFT)

            pct_open = Text(f"{(1-closed_ratio):.0%}", font_size=24, weight=BOLD, color=t.get("red", "#f85149"))
            lbl_open = Text("Open", font_size=16, color=t["sub"]).next_to(pct_open, DOWN, buff=0.1)
            open_grp = VGroup(pct_open, lbl_open).next_to(open_rect, UP, buff=0.4).align_to(open_rect, RIGHT)

            # Total Count Label
            total_lbl = Text(f"Total PRs: {total_prs}", font_size=20, color=t["text"]).next_to(track, DOWN, buff=0.8)

            # 3. Animation Sequence
            self.play(FadeIn(track), FadeIn(total_lbl))
            
            # Initial state for animation (scale from left/right)
            closed_rect.save_state()
            open_rect.save_state()
            closed_rect.stretch_to_fit_width(0.01).move_to(track.get_left(), aligned_edge=LEFT)
            open_rect.stretch_to_fit_width(0.01).move_to(track.get_right(), aligned_edge=RIGHT)

            self.play(
                closed_rect.animate.restore(),
                open_rect.animate.restore(),
                run_time=2,
                rate_func=slow_into
            )
            
            self.play(
                LaggedStart(
                    FadeIn(merged_grp, shift=UP * 0.3),
                    FadeIn(open_grp, shift=UP * 0.3),
                    lag_ratio=0.2
                )
            )

            self.wait(3)
            self.play(FadeOut(VGroup(bar_group, track, merged_grp, open_grp, total_lbl, pr_title)))

        # --- SCENE 8: Taxonomy Bar Chart ---
        if categories:
            bar_title = Text("Commit Taxonomy", font_size=36, color=t["text"]).to_edge(UP, buff=0.5)
            self.play(FadeIn(bar_title, shift=DOWN))
            
            cat_colors = {
                "feature": t.get("green", GREEN),
                "fix": t.get("red", RED),
                "refactor": t["accent"],
                "docs": t["sub"],
                "testing": t["primary"],
                "other": t["secondary"]
            }
            
            max_v = max(categories.values()) if categories else 1
            all_bars = VGroup()
            
            for name, val in categories.items():
                h = (val / max_v) * 4 
                color = cat_colors.get(name.lower(), t["primary"])
                
                val_text = Text(str(val), font_size=18, color=t["text"])
                bar_rect = Rectangle(width=1.2, height=max(h, 0.1), fill_color=color, fill_opacity=0.9, stroke_width=0)
                name_text = Text(name.title(), font_size=16, color=t["text"])
                
                bar_item = VGroup(val_text, bar_rect, name_text).arrange(DOWN, buff=0.2)
                all_bars.add(bar_item)
            
            if len(all_bars) > 0:
                all_bars.arrange(RIGHT, buff=0.8, aligned_edge=DOWN).shift(DOWN * 0.5)
                
                for i, bar_item in enumerate(all_bars):
                    val_text, bar_rect, name_text = bar_item
                    self.play(
                        FadeIn(name_text, shift=UP*0.2),
                        GrowFromEdge(bar_rect, DOWN),
                        FadeIn(val_text, shift=UP*0.2),
                        run_time=0.3
                    )
                
                self.wait(1.5)
                self.play(FadeOut(all_bars, shift=DOWN), FadeOut(bar_title, shift=UP))

        # --- SCENE 9: Line Graph (Commits Over Time) ---
        freq_timeline = data.get("commit_frequency_timeline", {})
        if freq_timeline:
            lg_title = Text("Commit Timeline", font_size=36, color=t["text"]).to_edge(UP, buff=0.5)
            self.play(FadeIn(lg_title))

            date_strs = list(freq_timeline.keys())
            try:
                dates = [datetime.datetime.strptime(d, "%Y-%m-%d").date() for d in date_strs]
            except Exception:
                dates = []
            
            if dates:
                start_date = dates[0]
                end_date = dates[-1]
                total_days = max(1, (end_date - start_date).days)
                
                counts = list(freq_timeline.values())
                max_count = max(counts) if counts else 1
                
                graph_w = 10
                graph_h = 4
                
                points = []
                for d, count in zip(dates, counts):
                    frac_x = (d - start_date).days / total_days
                    x = -graph_w/2 + frac_x * graph_w
                    y = -graph_h/2 + (count / max_count) * graph_h
                    points.append(np.array([x, y, 0]))
                
                lines = VGroup()
                dots = VGroup()
                for i in range(len(points)-1):
                    lines.add(Line(points[i], points[i+1], color=t["primary"], stroke_width=4))
                for p in points:
                    dots.add(Dot(p, color=t["accent"], radius=0.08))
                
                axes = VGroup(
                    Line(np.array([-graph_w/2, -graph_h/2, 0]), np.array([graph_w/2, -graph_h/2, 0]), color=t["secondary"], stroke_width=2),
                    Line(np.array([-graph_w/2, -graph_h/2, 0]), np.array([-graph_w/2, graph_h/2, 0]), color=t["secondary"], stroke_width=2)
                )
                
                start_label = Text(start_date.strftime("%b %Y"), font_size=16, color=t["sub"]).move_to(np.array([-graph_w/2, -graph_h/2 - 0.5, 0]))
                end_label = Text(end_date.strftime("%b %Y"), font_size=16, color=t["sub"]).move_to(np.array([graph_w/2, -graph_h/2 - 0.5, 0]))
                
                self.play(Create(axes), FadeIn(start_label), FadeIn(end_label))
                self.play(Create(lines, lag_ratio=1), run_time=3)
                self.play(FadeIn(dots, lag_ratio=0.1), run_time=1)
                
                self.wait(2)
                self.play(FadeOut(VGroup(axes, start_label, end_label, lines, dots, lg_title)))

        # --- SCENE 10: Contributor Bar Chart ---
        if contributors:
            cb_title = Text("Commits per Contributor", font_size=36, color=t["text"]).to_edge(UP, buff=0.5)
            self.play(FadeIn(cb_title))
            
            top_c = contributors[:6]
            max_c = max([c.get("commits", 0) for c in top_c]) if top_c else 1
            
            c_bars = VGroup()
            for c in top_c:
                count = c.get("commits", 0)
                name = c.get("name", "Unknown")
                w = (count / max_c) * 7 
                
                name_tex = Text(name[:12], font_size=20, color=t["text"])
                bar = Rectangle(height=0.4, width=max(w, 0.1), fill_color=t.get("green", GREEN), fill_opacity=0.8, stroke_width=0)
                val_tex = Text(str(count), font_size=18, color=t["accent"])
                
                row = VGroup(name_tex, bar, val_tex).arrange(RIGHT, buff=0.3)
                c_bars.add(row)
                
            if len(c_bars) > 0:
                c_bars.arrange(DOWN, buff=0.4, aligned_edge=LEFT).move_to(ORIGIN)
                
                max_name_w = max([row[0].width for row in c_bars]) if c_bars else 0
                for row in c_bars:
                    row[0].align_to(c_bars, LEFT)
                    row[0].shift(RIGHT * (max_name_w - row[0].width))
                    row[1].next_to(row[0], RIGHT, buff=0.3)
                    row[2].next_to(row[1], RIGHT, buff=0.3)
                    
                self.play(FadeIn(VGroup(*[row[0] for row in c_bars])))
                for row in c_bars:
                    orig_w = row[1].width
                    row[1].stretch_to_fit_width(0.01)
                    row[1].next_to(row[0], RIGHT, buff=0.3)
                    self.play(
                        row[1].animate.stretch_to_fit_width(orig_w).next_to(row[0], RIGHT, buff=0.3),
                        FadeIn(row[2]),
                        run_time=0.3
                    )
                
                self.wait(2)
                self.play(FadeOut(c_bars), FadeOut(cb_title))

        # --- SCENE 11: Contributor Heatmap ---
        heatmap_data = data.get("contributor_heatmap", {})
        if heatmap_data:
            hm_title = Text("Activity Heatmap", font_size=36, color=t["text"]).to_edge(UP, buff=0.5)
            self.play(FadeIn(hm_title))
            
            from manim.utils.color import ManimColor
            top_hm_users = list(heatmap_data.keys())[:4] 
            all_date_strs = []
            for u in top_hm_users:
                all_date_strs.extend(heatmap_data[u].keys())
                
            if all_date_strs:
                all_dates = [datetime.datetime.strptime(d, "%Y-%m-%d").date() for d in all_date_strs]
                min_d = min(all_dates)
                max_d = max(all_dates)
                total_days = (max_d - min_d).days
                
                cols = min(total_days + 1, 35) 
                
                hm_group = VGroup()
                for user in top_hm_users:
                    u_data = heatmap_data[user]
                    u_name = Text(user[:12], font_size=16, color=t["text"])
                    
                    squares = VGroup()
                    u_max = max(u_data.values()) if u_data else 1
                    
                    for i in range(cols):
                        start_day = (i / cols) * max(1, total_days)
                        end_day = ((i+1) / cols) * max(1, total_days)
                        
                        count = 0
                        for d_str, v in u_data.items():
                            d_obj = datetime.datetime.strptime(d_str, "%Y-%m-%d").date()
                            day_idx = (d_obj - min_d).days
                            if start_day <= day_idx <= end_day:
                                count += v
                                
                        intensity = min(count / (u_max + 0.001), 1.0)
                        
                        if count > 0:
                            c1 = ManimColor(t["secondary"])
                            c2 = ManimColor(t.get("green", GREEN))
                            sq_color = interpolate_color(c1, c2, intensity)
                        else:
                            sq_color = t["secondary"]
                            
                        sq = Square(side_length=0.25, fill_color=sq_color, fill_opacity=1, stroke_width=1, stroke_color=t["bg"])
                        squares.add(sq)
                        
                    if len(squares) > 0:
                        squares.arrange(RIGHT, buff=0.05)
                        row = VGroup(u_name, squares).arrange(RIGHT, buff=0.4)
                        hm_group.add(row)
                    
                if len(hm_group) > 0:
                    hm_group.arrange(DOWN, buff=0.3).move_to(ORIGIN)
                    
                    max_name_w = max([row[0].width for row in hm_group])
                    for row in hm_group:
                        row[0].align_to(hm_group, LEFT).shift(RIGHT * (max_name_w - row[0].width))
                        row[1].next_to(row[0], RIGHT, buff=0.4)
                        
                    self.play(FadeIn(hm_group, shift=UP))
                    self.wait(3)
                    self.play(FadeOut(hm_group), FadeOut(hm_title))

        # --- SCENE 12: Outro ---
        outro_title = Text("Repository Biography Complete", font_size=36, color=t["primary"])
        outro_sub = Text("Generated over the codebase timeline", font_size=20, color=t["sub"]).next_to(outro_title, DOWN, buff=0.3)
        outro_group = VGroup(outro_title, outro_sub).move_to(ORIGIN)
        
        self.play(FadeIn(outro_group, scale=1.2))
        self.wait(2)
        self.play(FadeOut(outro_group))