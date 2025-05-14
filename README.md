# Founder Movement Tracker

A tool that automates the detection of career changes among pre-seed founders. The application processes LinkedIn profiles from uploaded CSV files, detects when someone has changed their role to "Founder" or joined a stealth startup, and provides actionable insights for outreach.

## Features

- Upload and track LinkedIn profiles via CSV
- Automated detection of founder role changes
- AI-powered insights for outreach
- Integration with multiple APIs (Proxycurl, SerpApi, OpenAI)
- Google Sheets integration for data storage
- Email notifications for important changes

## Setup

1. Clone the repository
2. Create a virtual environment: \`python -m venv venv\`
3. Activate the virtual environment:
   - Windows: \`venv\\Scripts\\activate\`
   - Unix/MacOS: \`source venv/bin/activate\`
4. Install dependencies: \`pip install -r requirements.txt\`
5. Copy \`.env.example\` to \`.env\` and fill in your API keys
6. Run the application: \`streamlit run app.py\`

## Tech Stack

- Python 3.10+
- Streamlit
- Proxycurl API
- SerpApi
- OpenAI API
- Google Sheets API

## License

MIT
