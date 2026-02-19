# Deploy to GitHub — Sharp Sports Analysis

## Step 1: Create the Repository

1. Go to https://github.com/new
2. Repository name: `nfl-analytics-lab`
3. Description: `Sharp Sports Analysis — Research-driven NFL betting analytics suite`
4. Set to **Public** (so your friends can see it)
5. Do NOT add a README or .gitignore (we already have them)
6. Click **Create repository**

## Step 2: Push from Your Computer

Open **Command Prompt** or **PowerShell** and run:

```bash
cd "C:\Users\bmisa\OneDrive\Documents\P&B Concepts\NFL\WORK\nfl_analytics"

git init
git add -A
git commit -m "Sharp Sports Analysis NFL Analytics Lab v2.0"
git branch -M main
git remote add origin https://github.com/countryroads91/nfl-analytics-lab.git
git push -u origin main
```

**Note:** The `data_processed/nfl.duckdb` file (202MB) exceeds GitHub's 100MB limit. You have two options:

### Option A: Use Git LFS (recommended)
```bash
# Install Git LFS first: https://git-lfs.github.com/
git lfs install
git lfs track "*.duckdb"
git lfs track "*.parquet"
git add .gitattributes
git add -A
git commit -m "Add LFS tracking for large data files"
git push -u origin main
```

### Option B: Exclude data files
Keep the `.gitignore` as-is (it already excludes .duckdb and .parquet files). Your friends will need to run the data ingestion pipeline to build the database from the CSV files.

## Step 3: Share with Friends

Send them the link: `https://github.com/countryroads91/nfl-analytics-lab`

They'll need to:
1. Clone the repo
2. Get the Armchair Analysis CSV files (or you share the `data_processed/nfl.duckdb` file separately)
3. Run `pip install -r requirements.txt`
4. Run `streamlit run app/Home.py`

## Optional: Deploy to Streamlit Cloud (free hosting)

1. Go to https://share.streamlit.io/
2. Sign in with GitHub
3. Click "New app"
4. Select your `countryroads91/nfl-analytics-lab` repo
5. Main file path: `app/Home.py`
6. Click "Deploy"

Your friends can then access it via a web URL without installing anything!
