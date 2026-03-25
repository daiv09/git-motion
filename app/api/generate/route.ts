import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';
import fs from 'fs/promises';

const execAsync = promisify(exec);

export async function POST(req: Request) {
  try {
    const { url, quality = 'l' } = await req.json();

    if (!url) {
      return NextResponse.json({ error: 'URL is required' }, { status: 400 });
    }

    // 1. PATH SETUP
    // Use the absolute path you verified: /Library/Frameworks/Python.framework/Versions/3.13/bin/manim
    const manimPath = "/Library/Frameworks/Python.framework/Versions/3.13/bin/manim";
    const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';

    // Extract a safe folder name from URL
    const safeRepoPath = url.replace(/[^a-zA-Z0-9]/g, '_');
    const outputDir = path.join(process.cwd(), 'public', 'renders', safeRepoPath);
    const dataPath = path.join(outputDir, 'repo_data.json');
    const videoPath = path.join(outputDir, 'ProjectBiography.mp4');

    // Ensure directory exists
    await fs.mkdir(outputDir, { recursive: true });

    let data;
    let dataFetched = false;

    // 2. CACHING LOGIC
    try {
      await fs.access(dataPath);
      console.log(`Cache hit for ${dataPath}`);
      const dataContent = await fs.readFile(dataPath, 'utf-8');
      data = JSON.parse(dataContent);
      
      // Cache validation: Ensure new fields like 'analytics' are present
      if (data.analytics) {
        dataFetched = true;
        console.log(`Cache hit and valid for ${dataPath}`);
      } else {
        console.log(`Cache hit but invalid (missing analytics). Forcing fetch.`);
      }
    } catch (e) {
      console.log(`Cache miss for ${dataPath}. Fetching...`);
    }

    // 3. DATA FETCHING (Python Scraper)
    if (!dataFetched) {
      const pyScript = path.join(process.cwd(), 'backend', 'fetch_repo_data.py');
      try {
        console.log(`Executing Fetcher: ${pythonCmd} "${pyScript}" "${url}" "${outputDir}"`);
        const { stdout, stderr } = await execAsync(`"${pythonCmd}" "${pyScript}" "${url}" "${outputDir}"`, {
          cwd: process.cwd()
        });
        if (stderr) console.log('Fetch Logs:', stderr);
      } catch (execError: any) {
        console.error('Fetch execution failed:', execError);
        return NextResponse.json({ error: 'Failed to fetch GitHub data.' }, { status: 500 });
      }

      const dataContent = await fs.readFile(dataPath, 'utf-8');
      data = JSON.parse(dataContent);
    }

    // 4. VIDEO GENERATION (Manim Engine)
    const manimScript = path.join(process.cwd(), 'backend', 'manim_engine.py');
    const qualityFlag = quality === 'high' ? '-qh' : '-ql';

    // Command using absolute path to bypass venv restrictions
    const manimCommand = `${manimPath} "${manimScript}" ProjectBiography ${qualityFlag} --media_dir "${outputDir}"`;

    console.log(`Executing Manim: ${manimCommand}`);

    try {
      const { stdout, stderr } = await execAsync(manimCommand, {
        cwd: process.cwd(),
        env: {
          ...process.env,
          REPO_JSON_PATH: dataPath,
          // Inject the Python bin path into the shell environment
          PATH: `${process.env.PATH}:/Library/Frameworks/Python.framework/Versions/3.13/bin:/usr/local/bin:/opt/homebrew/bin`
        }
      });
      console.log('Manim output:', stdout);
    } catch (execError: any) {
      console.error('Manim execution failed:', execError);
      return NextResponse.json({ error: 'Manim render failed.' }, { status: 500 });
    }

    // 5. ASSET MANAGEMENT
    // Manim folder structure: {outputDir}/videos/{filename_without_py}/{resolution}/{ClassName}.mp4
    const resFolder = quality === 'high' ? '1080p60' : '480p15';
    const generatedVideoPath = path.join(
      outputDir,
      'videos',
      'manim_engine', // Derived from backend/manim_engine.py
      resFolder,
      'ProjectBiography.mp4' // Derived from class ProjectBiography(Scene)
    );

    // Copy the nested video to the easy-to-access root of the render folder
    try {
      await fs.copyFile(generatedVideoPath, videoPath);
      console.log("Success: Video moved to", videoPath);
    } catch (err) {
      console.error("Could not move video. Expected it at:", generatedVideoPath);
      return NextResponse.json({ error: 'Video file was generated but could not be located.' }, { status: 500 });
    }

    const videoUrl = `/renders/${safeRepoPath}/ProjectBiography.mp4`;
    return NextResponse.json({ ...data, videoUrl });

  } catch (error: any) {
    console.error('Server error:', error);
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 });
  }
}