# Breathe Pipeline

### The why

This project hits a couple of big themes for me. I was seeking out applications to practice BI and data engineering tools when Claude noted the connection with the Breathe app I deployed a few weeks ago. I have been collecting real data from that app and have been wanting some insights—especially after a recent flare-up that required an unusually large amount of inhaler usage. My hope is that I can inspire some exciting tool use and practice my skills with this deeply personal application.

## The architecture

Breathe app —> Google Sheets —> Python script extraction —> DuckDB —> dbt —> Evidence —> Netlify

* Breathe app: mobile app to collect symptom tracking and inhaler usage.
* Google Sheets: operational database to capture event records.
* Python script extraction: chosen as a simpler alternative than Airbyte for deployment.
* DuckDB: powerful analytics database that runs locally.
* dbt: transformational and semantic data layer.
* Evidence: clean and simple visualization tool that plugs into SQL databases and deploys as a static file.
* Netlify: hosting site which can be easily triggered from GitHub actions. 

### Stack
> Tools and versions once I know them.

### How to run
> Once it’s operational…

### Current status
*Where is the project… update after each session.*

> **Brainstormed design with Claude. Writing ideas into README.**

### Next action
*Literally just the next step or concrete action to take. Not a backlog or roadmap… just the next step. Overwrite this each time I work on the project.*

> **Put this into a project folder and make it a GitHub repository!**