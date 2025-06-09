# Ready the environment (In Windows)
- python -m venv .venv
- .venv\Scripts\activate
- pip install -r requirements.txt
- python run.py

# Ready the environment (In Mac or Linux)
- virtualenv -p python3 .venv
- source .venv/bin/activate
- pip install -r requirements.txt
- python run.py

# Instructions
1. Put your files inside 'inputs' folder. your files should consist of one source pdf and multiple appendix pdfs.

2. In config.json file set the name of your source and appendices files. in appendix section you should also write the placeholders name. Below is an example of config.json file

    ```
        {
            "source_file": "source.pdf",
            "appendices": [
                {
                    "file": "Appendix-A.pdf",
                    "placeholder": "[2.1 Environmental Loads]"
                },
                {
                    "file": "Appendix-B.pdf",
                    "placeholder": "[2.2 Blast Loads]"
                }
            ]
        }
    ```

3. You can find the result inside 'output' folder

4. Please make sure to put this text --> [page_#] in the header file instead of page numbers.