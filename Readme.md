# Personal Calendar Availability Renderer

This tool automatically generates a visual map of your **weekly calendar availability** for the next several weeks, using a subset of your Google Calendars. It renders the availability as:

- Static HTML tables (`availability_0.html`, `availability_1.html`, etc. for upcoming weeks)

The HTML files show **gray blocks for busy times** from Monday–Friday, 8am–6pm. It runs **once per day** after system login or wake using macOS `launchd`.

It pushes all this to your github web repo every day.

---

## 🔧 What's in This Repo

- `paul-cal.py`: Main script to pull calendar data and render HTML.
- `config_template.py`: Template configuration file that needs to be copied to `config.py` and customized
- `requirements.txt`: Python dependencies.
- `dev.availability.update.plist`: A sample `launchd` configuration file, edit and copy to ~/Library/LaunchAgents/

---

## 🚀 Installation Guide

### 1. **Set Up Google Calendar API Access**

You'll need to authorize access to your Google Calendars. Ask ChatGPT:

> "How do I enable the Google Calendar API and generate `credentials.json` to use with the Google API Python client? I'm the only one who needs access, and I'm setting myself up as a test user."

Briefly, the steps are:
- Go to https://console.cloud.google.com/
- Create a project, enable **Google Calendar API**
- Create **OAuth credentials** for a **Desktop App**
- Download the resulting `credentials.json`
- Place `credentials.json` in your project folder
- Run the script once manually to authorize and create `token.json`:
  ```bash
  python paul-cal.py
  ```

### 2. **Configure Your Settings**

Copy `config_template.py` to `config.py` and modify the following:
- `CALENDAR_NAMES = [...]` — include your own calendar names
- `TOKEN_PATH = '/absolute/path/to/token.json'`
- Output filenames and directories as needed

### 3. **Install Python Environment**

Set up a conda environment using the given requirements.txt:

```bash
conda create -n paul-cal python=3.11
conda activate paul-cal
pip install -r requirements.txt
```

### 4. **Set Up Auto-Run with launchd (macOS)**

This is another place to get help from ChatGPT to test and get right.

#### a. Edit the included `.plist` file:
Update this block to match your environment:

```xml
<key>ProgramArguments</key>
<array>
  <string>/full/path/to/python</string>
  <string>/full/path/to/paul-cal.py</string>
</array>
```

Example:
```xml
<string>/usr/local/Caskroom/miniconda/base/envs/paul-cal/bin/python</string>
<string>/Users/YOU/paul-cal/paul-cal.py</string>
```

#### b. Copy the plist to your user LaunchAgents folder:

```bash
cp dev.availability.update.plist ~/Library/LaunchAgents/
```

#### c. Load and schedule the job:

```bash
launchctl load ~/Library/LaunchAgents/dev.availability.update.plist
launchctl start dev.availability.update
```

#### d. Logs:

Check for errors here:
```bash
cat /tmp/availability.err
cat /tmp/availability.log
```

---

## ✅ What Happens

Every time you log in or wake your Mac, the script will:
- Connect to Google Calendar
- Check your selected calendars
- Generate/overwrite `availability.html`
- Push the HTML file to your github web repo

---

## ❓ Need Help?

Ask ChatGPT

