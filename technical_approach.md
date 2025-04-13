# Technical Approach: Enron Financial Fraud Detection

This document explains the methodology and implementation details of our approach to detecting financial fraud in the Enron email corpus, as implemented in `main.py`.

## Overview

Our approach uses a multi-tier prioritization system to identify emails that provide evidence of Enron's financial fraud, with a focus on Special Purpose Entities (SPEs), off-balance-sheet financing, and communications between key executives. The system combines weighted keyword analysis, executive communication patterns, and contextual clues to assign fraud scores to emails and identify the most suspicious communications.

## Data Processing Pipeline

The fraud detection pipeline consists of the following steps:

1. **Dataset Extraction and Loading**
2. **Email Content Analysis**
3. **Fraud Context Detection**
4. **Executive Communication Analysis**
5. **Comprehensive Fraud Scoring**
6. **Multi-tier Email Prioritization**
7. **Detailed Analysis Report Generation**

## 1. Dataset Extraction and Loading

The pipeline begins by extracting the Enron email dataset from a tar.gz archive if it hasn't been extracted already:

```python
def extract_enron_dataset():
    unzipped_folder = 'Enron_dataset'
    zip_file = 'enron_mail_20150507.tar.gz'

    if not os.path.exists(unzipped_folder):
        print(f"Folder '{unzipped_folder}' not found. Extracting '{zip_file}'.")
        try:
            with tarfile.open(zip_file, "r:gz") as tar:
                tar.extractall(unzipped_folder)
            print(f"Successfully extracted to '{unzipped_folder}'")
        except FileNotFoundError:
            print(f"Error: zipfile '{zip_file}' not found")
            return False
        except Exception as e:
            print(f"Error extracting file: {e}")
            return False
    return True
```

Emails are then parsed and loaded into a pandas DataFrame for analysis:

```python
def create_dataframe(document_type='all_documents'):
    csv_file = f"{document_type}.csv"
    
    if os.path.exists(csv_file):
        print(f"Loading saved DataFrame from {csv_file} from last time!")
        return pd.read_csv(csv_file)
    
    # If CSV doesn't exist, parse the emails and create a new DataFrame
    # ...
```

## 2. Fraud-Specific Keywords and Persons of Interest

We defined two key sets of data for our analysis:

### Weighted Fraud Keywords

Instead of using generic keywords, we created a weighted dictionary of terms specifically related to Enron's fraudulent practices:

```python
FRAUD_KEYWORDS_WEIGHTED = {
    # SPE-related terms (highest priority - these were central to the fraud)
    'ljm': 10,                  # LJM partnerships (Fastow's SPEs)
    'ljm1': 10,                 # LJM1 partnership
    'ljm2': 10,                 # LJM2 partnership
    'raptor': 10,               # Raptor vehicles used to hide losses
    'raptors': 10,              # Plural form
    'special purpose entity': 8, # Generic SPE term
    # ...
    
    # Smoking gun phrases (highest priority - direct evidence of intent)
    'don\'t put in writing': 10, # Clear intent to hide
    'don\'t leave a trail': 10,  # Clear intent to hide
    'verbal only': 9,           # Avoiding written record
    # ...
}
```

The weights (1-10) indicate the importance of each term as an indicator of fraud, with higher weights given to terms directly related to Enron's specific fraudulent structures.

### Fraud-Related Persons of Interest

We identified key executives and individuals involved in Enron's fraud:

```python
FRAUD_POIS = [
    'skilling', 'jeff.skilling', 'jeffrey.skilling',
    'fastow', 'andrew.fastow', 'andy.fastow',
    'lay', 'kenneth.lay', 'ken.lay',
    # ...
]
```

## 3. Fraud Context Detection

The `detect_fraud_context` function analyzes email content to identify fraud indicators:

```python
def detect_fraud_context(email_body, email_from=None, email_to=None, email_subject=None):
    # Initialize score
    score = 0
    
    # Skip if body is empty or not a string
    if not email_body or not isinstance(email_body, str):
        return score
    
    # Convert to lowercase for case-insensitive matching
    body = email_body.lower()
    
    # Check for fraud keywords with weighted importance
    for keyword, weight in FRAUD_KEYWORDS_WEIGHTED.items():
        if keyword.lower() in body:
            score += weight
    
    # Check for SPE-related terms
    spe_terms = ['ljm', 'raptor', 'spe', 'special purpose', 'chewco', 'jedi', 'whitewing']
    spe_count = sum(1 for term in spe_terms if term in body)
    if spe_count > 0:
        # Bonus for multiple SPE mentions
        score += 5 * spe_count
    
    # Additional checks for financial terms, suspicious phrases, subject line indicators...
    # ...
    
    # Prioritize internal Enron communications
    if email_from and email_to:
        from_field = str(email_from).lower()
        to_field = str(email_to).lower()
        
        # Internal communication (both from and to Enron)
        if '@enron.com' in from_field and '@enron.com' in to_field:
            score *= 1.5  # 50% boost for internal communications
    
    return score
```

This function assigns points based on:
- Presence of weighted fraud keywords
- Mentions of SPEs and financial terms
- Suspicious phrases indicating intent to hide information
- Subject line indicators
- Whether the communication is internal to Enron

## 4. Newsletter and External Report Filtering

To reduce false positives, we implemented a filter to identify and exclude newsletters and external reports:

```python
def is_newsletter_or_external_report(email_subject, email_from):
    # Check if subject exists
    if not email_subject or not isinstance(email_subject, str):
        return False
        
    # Convert to lowercase for case-insensitive matching
    subject = email_subject.lower()
    
    # Check for newsletter indicators in subject
    newsletter_indicators = [
        'newsletter', 'daily update', 'weekly update', 'news update',
        'press release', 'announcement', 'bulletin', 'report',
        # ...
    ]
    
    if any(indicator in subject for indicator in newsletter_indicators):
        return True
    
    # Check if from external source (not enron.com)
    if email_from and isinstance(email_from, str):
        from_field = email_from.lower()
        if '@enron.com' not in from_field:
            return True
    
    return False
```

## 5. Executive Communication Analysis

The `analyze_executive_communication` function scores emails based on communication patterns between key executives:

```python
def analyze_executive_communication(email_from, email_to, email_cc=None, email_body=None):
    # Initialize score
    score = 0
    
    # Skip if missing required fields
    if not email_from or not email_to:
        return score
    
    # Convert to lowercase for case-insensitive matching
    from_field = str(email_from).lower()
    to_field = str(email_to).lower()
    cc_field = str(email_cc).lower() if email_cc else ''
    
    # Define key executives with their name variations
    key_execs = {
        'fastow': ['andrew.fastow', 'andy.fastow', 'fastow'],
        'skilling': ['jeffrey.skilling', 'jeff.skilling', 'skilling'],
        # ...
    }
    
    # Check if from/to a key executive and assign scores
    # ...
    
    # Define high-value executive pairs (key players in fraud)
    high_value_pairs = [
        ('fastow', 'skilling'), ('fastow', 'lay'), ('fastow', 'causey'),
        # ...
    ]
    
    # Check if this is a high-value pair
    # ...
    
    # Check email body for suspicious content if communication involves executives
    # ...
    
    return score
```

This function:
- Identifies emails sent by or to key executives
- Gives higher scores to communications between specific executive pairs
- Assigns additional points when executives discuss SPEs or financial matters
- Checks for suspicious language in executive communications

## 6. Comprehensive Fraud Scoring

In the main function, we calculate a comprehensive fraud score by combining multiple factors:

```python
# Create comprehensive fraud score
df['FraudScore'] = 0

# Add context and executive communication scores
df['FraudScore'] += df['FraudContextScore']
df['FraudScore'] += df['ExecCommScore']

# Boost score for emails in critical periods
df.loc[df['CriticalPeriod'], 'FraudScore'] *= 1.5

# Boost score for emails that are part of threads
thread_mask = df['Subject'].str.contains('Re:|Fwd:', case=False, na=False)
df.loc[thread_mask, 'FraudScore'] *= 1.2

# Boost score for emails with attachments (could contain financial documents)
attachment_mask = df['X-FileName'].str.contains('xls|doc|pdf|ppt', case=False, na=False)
df.loc[attachment_mask, 'FraudScore'] *= 1.1
```

The scoring system incorporates:
- Content-based fraud indicators
- Executive communication patterns
- Temporal factors (critical periods in Enron's timeline)
- Thread information (replies may contain important context)
- Attachment presence (financial documents)

## 7. Multi-tier Email Prioritization

We implemented a sophisticated multi-tier prioritization system to identify the most relevant emails:

### First Priority: Internal Enron emails discussing SPEs AND financial manipulation

```python
# First priority: Internal Enron emails discussing SPEs AND financial manipulation
for _, email in top_emails.iterrows():
    # Skip newsletters and external reports
    if is_newsletter_or_external_report(email.get('Subject'), email.get('From')):
        continue
        
    # Check if it's an internal Enron communication
    # ...
    
    # Check for emails containing both SPE terms and financial manipulation terms
    spe_terms = ['ljm', 'raptor', 'spe', 'special purpose', 'chewco', 'jedi', 'whitewing']
    financial_terms = ['million', 'loss', 'hide', 'debt', 'off-balance', 'mark-to-market', 'mtm']
    
    # Prioritize internal communications about SPEs and financial manipulation
    if (any(spe.lower() in body.lower() for spe in spe_terms) and 
        any(term.lower() in body.lower() for term in financial_terms)):
        # Give higher priority to internal communications
        if is_internal_enron:
            final_top_emails = pd.concat([final_top_emails, pd.DataFrame([email])], ignore_index=True)
            if len(final_top_emails) >= 5:
                break
```

### Second Priority: Communications between key executives about sensitive topics

```python
# Second priority: Communications between key executives about sensitive topics
if len(final_top_emails) < 5:
    # ...
    
    # Check if email is between key executives
    # ...
    
    # Check for high-value executive pairs
    # ...
    
    # Check if it contains suspicious language
    smoking_gun_phrases = [
        'off the books', 'hide the loss', 'hide the debt', 'accounting problem',
        # ...
    ]
    
    # Prioritize communications between key executives with suspicious content
    if (is_high_value_pair and has_smoking_gun) or \
       (from_exec and to_exec and any(spe in body.lower() for spe in ['ljm', 'raptor', 'spe', 'chewco'])):
        # ...
```

### Third and Fourth Priorities

Similar logic is applied for:
- Third priority: Any internal Enron emails with high fraud scores
- Fourth priority: Any remaining high-scoring emails (with newsletters filtered out)

## 8. Detailed Analysis Report Generation

Finally, we generate a detailed analysis report for each flagged email:

```python
# Generate a detailed analysis report
with open('fraud_email_analysis.txt', 'w') as f:
    f.write("===== ENRON FRAUD EMAIL ANALYSIS =====\n\n")
    
    for i, (_, email) in enumerate(final_top_emails.iterrows(), 1):
        f.write(f"EMAIL #{i}:\n")
        f.write(f"From: {email.get('From') or 'Unknown'}\n")
        # ...
        
        f.write("ANALYSIS:\n")
        # Analyze why this email was flagged
        body = str(email.get('Body', ''))
        
        # Check for SPE terms
        spe_terms = ['ljm', 'raptor', 'spe', 'special purpose', 'chewco', 'jedi', 'whitewing']
        found_spes = [spe for spe in spe_terms if spe in body.lower()]
        if found_spes:
            f.write(f"- Contains SPE references: {', '.join(found_spes)}\n")
        
        # Additional analysis for financial terms, suspicious language, executive involvement
        # ...
        
        f.write("\nFULL EMAIL BODY:\n")
        f.write(f"{body}\n\n")
        f.write("-" * 80 + "\n\n")
```

This report includes:
- Email metadata (sender, recipient, date, subject)
- Fraud score
- Analysis of why the email was flagged
- Identified SPE references
- Financial terms found
- Suspicious language detected
- Executive involvement
- Full email body for context

## Conclusion

Our approach combines domain knowledge about Enron's specific fraudulent practices with sophisticated text analysis techniques to identify the most relevant emails. The multi-tier prioritization system ensures that the most suspicious emails—those discussing SPEs, financial manipulation, and communications between key executives—are surfaced first.

The effectiveness of this approach is demonstrated by the quality of the emails identified, which provide direct evidence of Enron's fraudulent financial structures and practices.
