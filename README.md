# ◈ Task Timeline Manager

A visual timeline tool for tracking tasks per person — horizontal axis with vertical branches per task, event nodes with collapsible detail cards and SharePoint links.

## What it looks like

- **Horizontal axis** across the screen with a date scale
- **Branches** shoot vertically (alternating up/down) from the axis — one per task
- **Nodes** on each branch represent events (emails, documents, meetings, etc.)
- **Click a node** → event card pops up with description + SharePoint link
- **Click again** → card collapses
- **Pan** by clicking and dragging, or scrolling horizontally

## Local setup

```bash
# 1. Clone your repo
git clone https://github.com/yourusername/task-timeline
cd task-timeline

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
streamlit run app.py
```


## How to use

### Adding a new task branch
1. Click **＋ New branch** in the sidebar
2. Fill in the person's name, task title, date, and initial note
3. Optionally paste a SharePoint link

### Adding an event to an existing branch
1. Click **＋** next to the branch name in the sidebar
2. Fill in the event details

### Sharing with teammates
- Deploy to Streamlit Cloud — share the URL
- The JSON data file is the source of truth; commit it to the repo for persistence
- Teammates with the URL can view the timeline; only you (with the running app) can add entries

## File structure

```
task-timeline/
├── app.py                  # Main Streamlit app
├── requirements.txt
├── timeline_data.json      # Your data (commit this!)
└── README.md
```

## Customisation tips

- **Colors**: Branch colors cycle through 6 presets. Edit the list in `app.py` (search for `color`) to change them.
- **Axis position**: Change `AXIS_Y_FRAC = 0.58` in the JS to move the axis up or down (0.5 = centre).
- **Branch height**: `branchH` auto-scales with event count. Adjust the formula to taste.
- **Date scale**: Currently shows monthly ticks. Change the `d.setMonth` loop to weekly if needed.
