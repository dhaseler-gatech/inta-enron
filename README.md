# Enron Financial Fraud Detection

This project analyzes the Enron email dataset to identify evidence of financial fraud, focusing on Special Purpose Entities (SPEs), off-balance sheet financing, and executive communications. It was developed for the INTA6450 course.

## Repository Contents

### Key Analysis Files

- **enron_fraud_email_analysis.md**: Detailed academic analysis of the five key emails with methodology, findings, and project questions
- **enron_fraud_emails_presentation.md**: Presentation-ready versions of the five key emails with evidence value explanations
- **enron_fraud_emails_evidence.md**: Focused analysis of the five most significant emails with complete metadata and evidence value
- **technical_approach.md**: Explanation of the methodology and implementation details
- **code_explanation.md**: Simplified explanation of the code's functionality with flow diagram

### Code Files

- **main.py**: The main Python script that processes the Enron dataset and identifies suspicious emails
- **requirements.txt**: List of Python packages required to run the project
- **fraud_email_analysis.txt**: Detailed analysis output from running main.py

## Setup

1. Clone this repository to your computer:
    ```bash
    git clone https://github.com/your-username/inta-enron.git
    ```

2. Download the dataset by visiting the following link:
    [Enron Mail Dataset](https://www.cs.cmu.edu/~./enron/enron_mail_20150507.tar.gz)

3. Move the downloaded `.tar.gz` file to the same directory where you cloned the repository, alongside `main.py`.

4. The initial run will take longer as it unzips the dataset and creates the necessary data frames. Once this process is complete, subsequent runs will be faster.

## Running the Project

Install the required packages
```bash
pip3 install -r requirements.txt
```

To run the project, simply execute the `main.py` script:
```bash
python3 main.py
```
