# Engage 2 Hackathon

## Information
This event will bring together new talents to the aviation industry for two days of intense collaboration and creativity. 
Participants will have the opportunity to tackle the industry’s digitalization challenge, 
featuring a 24-hour coding session to tackle proposed ATM-related challenges.

https://wikiengagektn.com/hackathons/

## Repository set-up
Once this repository has been cloned for the first time in a new machine, you need to sync all the submodules.
Launch these commands from the repository root directory:

```shell
git submodule init
git submodule sync
git submodule update
```

## Repository update
To pull (update) all git changes from this repository and all its submodules:

```bash
# First, update the main branch
git pull

# Then, update the submodules (recursively)
git submodule update --recursive --remote
```

## Python virtual environment

If your project uses Python, you will need to set up a virtual environment.
If you are using an IDE, it will take care of it.
If you are running this repo from a server, you will need to create it manually:

```bash
python3 -m venv venv
```

> This step only needs to be done once.

Then, each time you want to load the venv:

```bash
source venv/bin/activate
```

With the venv loaded, install any python requirements in your project:

```bash
pip3 install -r requirements.txt
```

---

## Instructions to run the campaign \<INSERT NAME OF THE CAMPAIGN HERE>

### Traceability
- Trello card: \<URL HERE>
- Main repository tag: \<TAG NAME HERE>
- Release of XXXX: \<RELEASE PATH HERE>
- etc.

### Checklist before campaign launch
- Ensure there are no commits pending in project's repository.
- Create new cases folder and ensure it's clean (`/icarus/cases/<your_project>/<campaign-xxx>`)
- Main launch script is calling `traceability.sh` and point the output to the cases folder of this campaign.

### Step 01: \<SHORT DESCRIPTION>
Long description about which specific script to execute, how to execute it, 
which cmd arguments to use, and any additional steps or information. 
Use absolute paths for everything.

> Some footnotes about extra stuff to take into account.

### Step 02: \<SHORT DESCRIPTION>
etc.
