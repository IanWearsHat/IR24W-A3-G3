# IR24W-A3-G3

Group Members
-------------------------
Ian Dai - idai - 80419415

Xiao Du - xdu7 - 56714415

Henry Wang - penghanw - 85703671

-------------------------

## For Python code:

Ensure [Python](https://www.python.org/downloads/) is installed

1. Run 
```bash
cd api
```

2. Create a virtual environment so that dependencies do not conflict
```bash
python -m venv .venv
```

3. Activate virtual environment

   VS Code may prompt to automatically select the newly created virtual environment.
   Otherwise, for Mac/Linux, run

   ```shell
   source .venv/bin/activate
   ```
   and for Windows, run

   ```shell
   .\.venv\scripts\activate
   ```

3. To install dependencies, run
```bash
pip install -r requirements.txt
```

You can now run any python code.

## For creating index
Ensure you are in the root directory and that you have the all of the webpages in one folder labeled "DEV" in the indexer folder

Like so:

![Indexer folder structure](https://i.imgur.com/ZeaYNST.png)

To start creating the index, run
```bash
python indexer\indexer.py
```

or
```bash
python3 indexer\indexer.py
```

## For backend:
1. From root directory

Run
```bash
cd api
cd src
```

2. Run
```bash
python main.py
```

or 
```bash
python3 main.py
```


## For Frontend:
1. Install Node and npm [here](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm).

2. 
From root directory

Run
```bash
cd front
```

Run
```bash
npm install
```

Run
```bash
npm run dev
```

A server will start at http://localhost:5173/ (or 127.0.0.1:5173)

## Making a query
Open a browser and navigate to http://localhost:5173/ (or 127.0.0.1:5173)

The page should look something like this

![Search engine home](https://i.imgur.com/LYsWQSO.png)

Simply enter a query into the search bar at the top and click Search
