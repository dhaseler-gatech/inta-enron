import os
import tarfile
import pandas as pd
import re
import numpy as np
from collections import Counter
import nltk
from nltk.corpus import stopwords
from tqdm import tqdm  # Add progress bar
nltk.download('stopwords')

def extract_enron_dataset():
    unzipped_folder = 'Enron_dataset'
    zip_file = 'enron_mail_20150507.tar.gz'

    if not os.path.exists(unzipped_folder):
        print(f"Folder '{unzipped_folder}' not found. Extracting '{zip_file}'.")
        try:
            import tarfile
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

# Define fraud-specific keywords based on Enron's actual fraudulent practices
# With weighted importance (higher values = more important indicators of fraud)
FRAUD_KEYWORDS_WEIGHTED = {
    # SPE-related terms (highest priority - these were central to the fraud)
    'ljm': 10,                  # LJM partnerships (Fastow's SPEs)
    'ljm1': 10,                 # LJM1 partnership
    'ljm2': 10,                 # LJM2 partnership
    'raptor': 10,               # Raptor vehicles used to hide losses
    'raptors': 10,              # Plural form
    'special purpose entity': 8, # Generic SPE term
    'special purpose vehicle': 8, # Generic SPV term
    'spe': 8,                   # Acronym
    'spv': 8,                   # Acronym
    'chewco': 9,                # SPE that violated accounting rules
    'jedi': 9,                  # Joint Energy Development Investments
    'whitewing': 9,             # Another SPE
    'condor': 7,                # Another Enron vehicle
    'talon': 7,                 # Another Enron vehicle
    
    # Accounting manipulation terms (high priority)
    'mark-to-market': 8,        # Accounting method abused by Enron
    'mtm': 8,                   # Acronym
    'mark to market': 8,        # Alternative spelling
    'off-balance': 9,           # Off-balance sheet transactions
    'off balance': 9,           # Alternative spelling
    'hide losses': 10,          # Direct indication of fraud
    'hide debt': 10,            # Direct indication of fraud
    'book value': 6,            # Accounting term
    'present value': 6,         # Accounting term
    'accounting issue': 7,      # Euphemism for problems
    'accounting problem': 7,    # Euphemism for problems
    'restructure debt': 7,      # Method used to conceal issues
    'arthur andersen': 6,       # Enron's auditor
    
    # Smoking gun phrases (highest priority - direct evidence of intent)
    'don\'t put in writing': 10, # Clear intent to hide
    'don\'t leave a trail': 10,  # Clear intent to hide
    'verbal only': 9,           # Avoiding written record
    'destroy document': 10,     # Document destruction
    'shred': 10,                # Document destruction
    'offline discussion': 8,    # Avoiding official channels
    'keep this quiet': 9,       # Secrecy
    'between us': 8,            # Secrecy
    'not for distribution': 7,  # Limited sharing
    'confidential': 6,          # Secrecy indicator
    'eyes only': 8,             # Limiting information
    
    # Financial manipulation (medium-high priority)
    'earnings management': 7,   # Euphemism for manipulation
    'aggressive accounting': 8, # Euphemism for manipulation
    'inflate revenue': 9,       # Direct indication of fraud
    'inflate earnings': 9,      # Direct indication of fraud
    'inflate profit': 9,        # Direct indication of fraud
    'cook the books': 10,       # Direct indication of fraud
    'financial engineering': 7, # Euphemism for manipulation
    'creative accounting': 8,   # Euphemism for manipulation
    'accounting trick': 8,      # Euphemism for manipulation
    'accounting loophole': 7    # Euphemism for manipulation
}

# Convert to list for compatibility with existing code
FRAUD_KEYWORDS = list(FRAUD_KEYWORDS_WEIGHTED.keys())

# Key executives and people involved in fraud
FRAUD_POIS = [
    'skilling', 'jeff.skilling', 'jeffrey.skilling',
    'lay', 'ken.lay', 'kenneth.lay',
    'fastow', 'andrew.fastow', 'andy.fastow',
    'causey', 'rick.causey', 'richard.causey',
    'delainey', 'david.delainey', 'dave.delainey',
    'kopper', 'michael.kopper', 'mike.kopper',
    'mcmahon', 'jeffrey.mcmahon', 'jeff.mcmahon',
    'arthur andersen', 'andersen', 'duncan', 'david.duncan'
]
def parse_email(content):
    headers = {
        'Message-ID': r'Message-ID:\s*(.*)',
        'Date': r'Date:\s*(.*)',
        'From': r'From:\s*(.*)',
        'To': r'To:\s*(.*)',
        'Subject': r'Subject:\s*(.*)',
        'Mime-Version': r'Mime-Version:\s*(.*)',
        'Content-Type': r'Content-Type:\s*(.*)',
        'Content-Transfer-Encoding': r'Content-Transfer-Encoding:\s*(.*)',
        'X-From': r'X-From:\s*(.*)',
        'X-To': r'X-To:\s*(.*)',
        'X-cc': r'X-cc:\s*(.*)',
        'X-bcc': r'X-bcc:\s*(.*)',
        'X-Folder': r'X-Folder:\s*(.*)',
        'X-Origin': r'X-Origin:\s*(.*)',
        'X-FileName': r'X-FileName:\s*(.*)'
    }

    # Improved body extraction
    header_end = re.search(r'\n\n', content)
    if header_end:
        header_part = content[:header_end.start()]
        body_part = content[header_end.end():]
    else:
        header_part = content
        body_part = None

    # Parse headers
    extracted_data = {key: None for key in headers}
    for key, pattern in headers.items():
        match = re.search(pattern, header_part, re.MULTILINE | re.IGNORECASE)
        extracted_data[key] = match.group(1).strip() if match else None

    # Clean body
    if body_part:
        body_part = re.sub(r'\n+', ' ', body_part).strip()
    extracted_data['Body'] = body_part
    
    return extracted_data


def create_dataframe(document_type='all_documents'):
    dataset_folder = 'Enron_dataset'
    csv_file = f"{document_type}.csv"

    if os.path.exists(csv_file):
        print(f"Loading saved DataFrame from {csv_file} from last time!")
        return pd.read_csv(csv_file)
    print(f"Dataframe not made yet for  {document_type}, building now (will take a sec!)")

    data = []
    for root, dirs, files in tqdm(list(os.walk(dataset_folder)), desc='Processing folders'):
        if document_type in root:
            person_folder = os.path.basename(os.path.dirname(root))
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    email_data = parse_email(content)
                    email_data['Person'] = person_folder
                    data.append(email_data)
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")

    df = pd.DataFrame(data)
    df = df.drop_duplicates(subset=['Message-ID', 'Body'])
    df.to_csv(csv_file, index=False)
    print(f"Saved DataFrame to {csv_file}")
    return df


# Enhanced filtering function
def filter_emails(df, keywords=None, pois=None, label='Body'):
    filtered_df = df.copy()
    if keywords:
        keyword_pattern = '|'.join([re.escape(k) for k in keywords])
        filtered_df = filtered_df[
            filtered_df[label].str.contains(keyword_pattern, case=False, na=False)
        ]
    if pois and label != 'Body':
        poi_pattern = '|'.join([re.escape(p) for p in pois])
        filtered_df = filtered_df[
            filtered_df[label].str.contains(poi_pattern, case=False, na=False)
        ]
    return filtered_df




def is_newsletter_or_external_report(email_subject, email_from):
    """Identify if an email is likely a newsletter, press report, or external communication"""
    if not email_subject or not isinstance(email_subject, str):
        return False
        
    # Common newsletter/report patterns in subject lines
    newsletter_patterns = [
        'press report', 'newsletter', 'news update', 'daily report', 'weekly report',
        'press release', 'news alert', 'market update', 'industry update', 'bulletin',
        'alumni', 'digest', 'news summary', 'daily news', 'weekly news'
    ]
    
    # Check subject line for newsletter patterns
    if any(pattern.lower() in email_subject.lower() for pattern in newsletter_patterns):
        return True
        
    # Check if from external sources (not enron.com)
    if email_from and isinstance(email_from, str):
        if '@enron.com' not in email_from.lower() and any(ext in email_from.lower() for ext in ['@isda.org', '@haas.berkeley.edu', '@newsletter', '@news', '@press']):
            return True
            
    return False


def detect_fraud_context(email_body, email_from=None, email_to=None, email_subject=None):
    """Score an email based on fraud-related contextual clues and communication patterns"""
    if not email_body or not isinstance(email_body, str):
        return 0
    
    score = 0
    
    # Skip newsletters and external reports
    if is_newsletter_or_external_report(email_subject, email_from):
        return 0  # Give zero score to newsletters/external reports
    
    # Prioritize internal Enron communications
    is_internal_enron = False
    if email_from and '@enron.com' in str(email_from).lower():
        if email_to and '@enron.com' in str(email_to).lower():
            is_internal_enron = True
            score += 5  # Bonus for internal Enron communications
    
    # Use the weighted keywords for more precise scoring
    for term, weight in FRAUD_KEYWORDS_WEIGHTED.items():
        if term.lower() in email_body.lower():
            score += weight
            
            # Extra points for key terms in internal communications
            if is_internal_enron and weight >= 8:
                score += 3  # Bonus when high-value terms appear in internal emails
    
    # Check for smoking gun phrases - these are the most incriminating
    smoking_gun_phrases = [
        'off the books', 'hide the loss', 'hide the debt', 'accounting problem',
        'don\'t put in writing', 'keep this quiet', 'between us', 'no trail',
        'avoid disclosure', 'circumvent', 'get around', 'cover up', 'bury the',
        'make it disappear', 'no one will know', 'won\'t be discovered'
    ]
    
    for phrase in smoking_gun_phrases:
        if phrase.lower() in email_body.lower():
            score += 12  # Very high score for smoking gun phrases
            
            # Even higher if in internal communication
            if is_internal_enron:
                score += 8  # Additional bonus
    
    # Check subject line for fraud indicators
    if email_subject and isinstance(email_subject, str):
        for term, weight in FRAUD_KEYWORDS_WEIGHTED.items():
            if term.lower() in email_subject.lower():
                score += weight * 1.5  # Higher weight for terms in subject line
    
    # Check for combinations of SPE terms with financial impact terms
    spe_terms = ['ljm', 'raptor', 'spe', 'special purpose', 'chewco', 'jedi', 'whitewing']
    financial_impact_terms = ['million', 'loss', 'debt', 'hide', 'off-balance', 'conceal']
    
    if any(spe.lower() in email_body.lower() for spe in spe_terms) and \
       any(term.lower() in email_body.lower() for term in financial_impact_terms):
        score += 15  # Very high score for SPE + financial impact combinations
    
    return score


def analyze_executive_communication(email_from, email_to, email_cc=None, email_body=None):
    """Score emails based on communication patterns between key executives"""
    if not email_from or not isinstance(email_from, str):
        return 0
    
    score = 0
    
    # Key executives involved in fraud
    key_executives = {
        'fastow': 5,       # Andrew Fastow (CFO) - created the SPEs
        'skilling': 4,      # Jeffrey Skilling (CEO)
        'lay': 4,           # Kenneth Lay (CEO/Chairman)
        'causey': 4,        # Rick Causey (Chief Accounting Officer)
        'delainey': 3,      # David Delainey (CEO of Enron Energy Services)
        'kopper': 3,        # Michael Kopper (Fastow's aide)
        'mcmahon': 2,       # Jeffrey McMahon (Treasurer)
        'glisan': 3,        # Ben Glisan (Treasurer)
        'duncan': 2,        # David Duncan (Arthur Andersen partner)
        'mintz': 2,         # Jordan Mintz (General Counsel)
        'derrick': 2,       # James Derrick (General Counsel)
        'buy': 2            # Rick Buy (Chief Risk Officer)
    }
    
    # Check if email is from a key executive
    for exec_name, exec_weight in key_executives.items():
        if exec_name.lower() in email_from.lower():
            score += exec_weight
            break
    
    # Check if email is to a key executive
    if email_to and isinstance(email_to, str):
        for exec_name, exec_weight in key_executives.items():
            if exec_name.lower() in email_to.lower():
                score += exec_weight - 1  # Slightly lower weight for recipient
                break
    
    # Check if email is CC'd to a key executive
    if email_cc and isinstance(email_cc, str):
        for exec_name in key_executives:
            if exec_name.lower() in email_cc.lower():
                score += 1  # Lower weight for CC
                break
    
    # High-value executive pairs (communications between these pairs are particularly suspicious)
    executive_pairs = [
        ('fastow', 'skilling'),   # CFO to CEO
        ('fastow', 'lay'),        # CFO to Chairman
        ('fastow', 'causey'),     # CFO to CAO
        ('fastow', 'kopper'),     # CFO to his aide
        ('fastow', 'glisan'),     # CFO to Treasurer
        ('causey', 'skilling'),   # CAO to CEO
        ('causey', 'arthur andersen'), # CAO to auditor
        ('delainey', 'skilling'),  # EES CEO to CEO
        ('mcmahon', 'fastow')      # Treasurer to CFO
    ]
    
    # Check for communications between executive pairs
    if email_to and isinstance(email_to, str):
        for exec1, exec2 in executive_pairs:
            if ((exec1.lower() in email_from.lower() and exec2.lower() in email_to.lower()) or
                (exec2.lower() in email_from.lower() and exec1.lower() in email_to.lower())):
                score += 6  # High score for suspicious executive pairs
                break
    
    # Additional score for suspicious content in executive communications
    if score > 0 and email_body and isinstance(email_body, str):
        suspicious_phrases = [
            'keep this between us', 'don\'t share', 'confidential', 'off the record',
            'not for distribution', 'eyes only', 'verbal discussion', 'no paper trail'
        ]
        
        for phrase in suspicious_phrases:
            if phrase.lower() in email_body.lower():
                score += 4  # Bonus for suspicious phrases in executive communications
                break
    
    return score


# Main execution
def main():
    """
    Main function for Enron Financial Fraud Detection.
    
    This function orchestrates the entire fraud detection pipeline:
    1. Loads the Enron email dataset
    2. Analyzes emails for fraud context and executive communication patterns
    3. Filters emails with fraud indicators
    4. Calculates comprehensive fraud scores based on multiple factors
    5. Identifies the most suspicious emails using a multi-tier prioritization system
    6. Generates detailed analysis reports
    
    The analysis focuses on identifying emails related to:
    - Special Purpose Entities (SPEs) like LJM, Raptor, Chewco, JEDI
    - Communications between key executives (Fastow, Skilling, Lay, etc.)
    - Discussions of accounting manipulation and financial fraud
    - Suspicious language indicating intent to hide information
    
    Results are saved to:
    - top_fraud_emails.csv: Raw data of the top suspicious emails
    - fraud_email_analysis.txt: Detailed analysis of each suspicious email
    """
    print("\n===== ENRON FINANCIAL FRAUD DETECTION =====\n")
    
    # Load data
    print("Step 1: Loading dataset...")
    extract_enron_dataset()
    df = create_dataframe()
    
    # Add fraud context score with enhanced analysis
    print("\nStep 2: Analyzing emails for fraud context and communication patterns...")
    
    # Apply enhanced context detection with more parameters
    print("  - Analyzing email content for fraud indicators...")
    df['FraudContextScore'] = df.apply(
        lambda row: detect_fraud_context(
            row['Body'], 
            email_from=row.get('From'), 
            email_to=row.get('To'), 
            email_subject=row.get('Subject')
        ), 
        axis=1
    )
    
    # Analyze executive communication patterns
    print("  - Analyzing executive communication patterns...")
    df['ExecCommScore'] = df.apply(
        lambda row: analyze_executive_communication(
            row.get('From', ''), 
            row.get('To', ''), 
            row.get('X-cc', ''), 
            row.get('Body', '')
        ),
        axis=1
    )
    
    # Filter by keywords and POIs
    print("\nStep 3: Filtering emails with fraud indicators...")
    keyword_emails = filter_emails(df, keywords=FRAUD_KEYWORDS, label='Body')
    print(f"  - Found {len(keyword_emails)} emails containing fraud keywords")
    
    poi_emails = filter_emails(df, pois=FRAUD_POIS, label='From')
    print(f"  - Found {len(poi_emails)} emails from key executives")
    
    # Combine and prioritize emails
    suspect_emails = pd.concat([keyword_emails, poi_emails]).drop_duplicates()
    
    # Add time-based analysis - focus on critical periods without datetime parsing
    # Instead of parsing dates, we'll use string matching for year/month patterns
    
    # Initialize critical period flag
    df['CriticalPeriod'] = False
    
    # Define critical period patterns (year-month)
    critical_patterns = [
        '2000-10', '2000-11',  # Q3 2000 earnings release period
        '2001-03', '2001-04',  # Q1 2001 earnings period
        '2001-08',             # Skilling resignation (Aug 14, 2001)
        '2001-10', '2001-11',  # Q3 2001 restatement period
        '2001-12'              # Bankruptcy period (Dec 2, 2001)
    ]
    
    # Flag emails during critical periods using string matching
    if 'Date' in df.columns:
        # Convert to string to ensure we can do string operations
        df['DateStr'] = df['Date'].astype(str)
        
        # Mark emails in critical periods
        for pattern in critical_patterns:
            mask = df['DateStr'].str.contains(pattern, na=False)
            df.loc[mask, 'CriticalPeriod'] = True
    
    # Create comprehensive fraud score
    print("\nStep 4: Calculating comprehensive fraud scores...")
    
    # Start with base score of 0
    df['FraudScore'] = 0
    
    # Add context and executive communication scores
    df['FraudScore'] += df['FraudContextScore']
    df['FraudScore'] += df['ExecCommScore']
    
    # Boost score for emails in critical periods
    df.loc[df['CriticalPeriod'], 'FraudScore'] *= 1.5
    
    # Boost score for emails that are part of threads
    # Look for Re: and Fwd: in subject lines
    if 'Subject' in df.columns:
        thread_mask = df['Subject'].str.contains('Re:|Fwd:', case=False, na=False)
        df.loc[thread_mask, 'FraudScore'] *= 1.2
    
    # Boost score for emails with attachments (could contain financial documents)
    if 'X-FileName' in df.columns:
        attachment_mask = df['X-FileName'].str.contains('xls|doc|pdf|ppt', case=False, na=False)
        df.loc[attachment_mask, 'FraudScore'] *= 1.1
    
    # Print score distribution statistics
    score_stats = df['FraudScore'].describe()
    print(f"  - Score statistics: Mean={score_stats['mean']:.1f}, Max={score_stats['max']:.1f}")
    print(f"  - Number of high-scoring emails (>20): {len(df[df['FraudScore'] > 20])}")
    
    # Get top suspicious emails
    print("\nStep 5: Identifying most suspicious emails...")
    top_emails = df.sort_values('FraudScore', ascending=False).head(50)
    
    # Enhanced filtering for most relevant emails
    print("  - Filtering for emails with substantive fraud evidence...")
    final_top_emails = pd.DataFrame()
    
    # First priority: Internal Enron emails discussing SPEs AND financial manipulation
    print("  - Looking for internal Enron emails discussing SPEs and financial manipulation...")
    for _, email in top_emails.iterrows():
        # Skip newsletters and external reports
        if is_newsletter_or_external_report(email.get('Subject'), email.get('From')):
            continue
            
        # Check if it's an internal Enron communication
        from_field = str(email.get('From', '')).lower()
        to_field = str(email.get('To', '')).lower()
        is_internal_enron = '@enron.com' in from_field and '@enron.com' in to_field
        
        body = email.get('Body')
        if body and isinstance(body, str):
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
    
    # Second priority: Communications between key executives about sensitive topics
    if len(final_top_emails) < 5:
        print(f"  - Found {len(final_top_emails)} emails so far, looking for executive communications...")
        remaining = top_emails[~top_emails.index.isin(final_top_emails.index)]
        for _, email in remaining.iterrows():
            # Skip newsletters and external reports
            if is_newsletter_or_external_report(email.get('Subject'), email.get('From')):
                continue
                
            from_field = str(email.get('From', '')).lower()
            to_field = str(email.get('To', '')).lower()
            body = str(email.get('Body', ''))
            
            # Check if email is between key executives (more specific check)
            key_execs = {
                'fastow': ['andrew.fastow', 'andy.fastow', 'fastow'],
                'skilling': ['jeffrey.skilling', 'jeff.skilling', 'skilling'],
                'lay': ['kenneth.lay', 'ken.lay', 'lay'],
                'causey': ['richard.causey', 'rick.causey', 'causey'],
                'delainey': ['david.delainey', 'dave.delainey', 'delainey'],
                'kopper': ['michael.kopper', 'mike.kopper', 'kopper'],
                'mcmahon': ['jeffrey.mcmahon', 'jeff.mcmahon', 'mcmahon'],
                'glisan': ['ben.glisan', 'glisan']
            }
            
            # Check if from a key executive
            from_exec = None
            for exec_name, variants in key_execs.items():
                if any(variant in from_field for variant in variants):
                    from_exec = exec_name
                    break
            
            # Check if to a key executive
            to_exec = None
            for exec_name, variants in key_execs.items():
                if any(variant in to_field for variant in variants):
                    to_exec = exec_name
                    break
            
            # Check for high-value executive pairs
            high_value_pairs = [
                ('fastow', 'skilling'), ('fastow', 'lay'), ('fastow', 'causey'),
                ('causey', 'skilling'), ('delainey', 'skilling'), ('fastow', 'kopper')
            ]
            
            is_high_value_pair = False
            if from_exec and to_exec:
                if (from_exec, to_exec) in high_value_pairs or (to_exec, from_exec) in high_value_pairs:
                    is_high_value_pair = True
            
            # Check if it contains suspicious language
            smoking_gun_phrases = [
                'off the books', 'hide the loss', 'hide the debt', 'accounting problem',
                'don\'t put in writing', 'keep this quiet', 'between us', 'no trail',
                'avoid disclosure', 'circumvent', 'get around', 'cover up'
            ]
            has_smoking_gun = any(phrase in body.lower() for phrase in smoking_gun_phrases)
            
            # Prioritize communications between key executives with suspicious content
            if (is_high_value_pair and has_smoking_gun) or \
               (from_exec and to_exec and any(spe in body.lower() for spe in ['ljm', 'raptor', 'spe', 'chewco'])):
                final_top_emails = pd.concat([final_top_emails, pd.DataFrame([email])], ignore_index=True)
                if len(final_top_emails) >= 5:
                    break
    
    # Third priority: Any internal Enron emails with high fraud scores
    if len(final_top_emails) < 5:
        print(f"  - Found {len(final_top_emails)} emails so far, looking for other internal emails with high fraud scores...")
        remaining = top_emails[~top_emails.index.isin(final_top_emails.index)]
        
        # Filter for internal Enron emails
        internal_emails = []
        for _, email in remaining.iterrows():
            from_field = str(email.get('From', '')).lower()
            to_field = str(email.get('To', '')).lower()
            
            if '@enron.com' in from_field and not is_newsletter_or_external_report(email.get('Subject'), email.get('From')):
                internal_emails.append(email)
        
        # Convert to DataFrame and take top emails
        if internal_emails:
            internal_df = pd.DataFrame(internal_emails)
            needed = 5 - len(final_top_emails)
            final_top_emails = pd.concat([final_top_emails, internal_df.head(needed)], ignore_index=True)
    
    # Fourth priority: Any remaining high-scoring emails if we still don't have 5
    if len(final_top_emails) < 5:
        print(f"  - Found {len(final_top_emails)} emails so far, adding remaining high-scoring emails...")
        remaining = top_emails[~top_emails.index.isin(final_top_emails.index)]
        
        # Filter out newsletters and external reports
        filtered_remaining = []
        for _, email in remaining.iterrows():
            if not is_newsletter_or_external_report(email.get('Subject'), email.get('From')):
                filtered_remaining.append(email)
        
        if filtered_remaining:
            filtered_df = pd.DataFrame(filtered_remaining)
            needed = 5 - len(final_top_emails)
            final_top_emails = pd.concat([final_top_emails, filtered_df.head(needed)], ignore_index=True)
    
    # Save results
    final_top_emails.to_csv('top_fraud_emails.csv', index=False)
    
    # Generate a detailed analysis report
    with open('fraud_email_analysis.txt', 'w') as f:
        f.write("===== ENRON FRAUD EMAIL ANALYSIS =====\n\n")
        
        for i, (_, email) in enumerate(final_top_emails.iterrows(), 1):
            f.write(f"EMAIL #{i}:\n")
            f.write(f"From: {email.get('From') or 'Unknown'}\n")
            f.write(f"To: {email.get('To') or 'Unknown'}\n")
            f.write(f"Date: {email.get('Date') or 'Unknown'}\n")
            f.write(f"Subject: {email.get('Subject') or 'No Subject'}\n")
            f.write(f"Fraud Score: {email.get('FraudScore', 0):.1f}\n\n")
            
            f.write("ANALYSIS:\n")
            # Analyze why this email was flagged
            body = str(email.get('Body', ''))
            
            # Check for SPE terms
            spe_terms = ['ljm', 'raptor', 'spe', 'special purpose', 'chewco', 'jedi', 'whitewing']
            found_spes = [spe for spe in spe_terms if spe in body.lower()]
            if found_spes:
                f.write(f"- Contains SPE references: {', '.join(found_spes)}\n")
            
            # Check for financial terms
            financial_terms = ['million', 'loss', 'hide', 'debt', 'off-balance', 'mark-to-market']
            found_terms = [term for term in financial_terms if term in body.lower()]
            if found_terms:
                f.write(f"- Contains financial terms: {', '.join(found_terms)}\n")
            
            # Check for suspicious language
            suspicious_terms = ['confidential', 'private', 'between us', 'not for distribution']
            found_suspicious = [term for term in suspicious_terms if term in body.lower()]
            if found_suspicious:
                f.write(f"- Contains suspicious language: {', '.join(found_suspicious)}\n")
            
            # Check if from/to key executives
            key_execs = ['fastow', 'skilling', 'lay', 'causey', 'delainey']
            from_field = str(email.get('From', '')).lower()
            to_field = str(email.get('To', '')).lower()
            
            from_execs = [exec_name for exec_name in key_execs if exec_name in from_field]
            to_execs = [exec_name for exec_name in key_execs if exec_name in to_field]
            
            if from_execs:
                f.write(f"- From key executive(s): {', '.join(from_execs)}\n")
            if to_execs:
                f.write(f"- To key executive(s): {', '.join(to_execs)}\n")
            
            f.write("\nFULL EMAIL BODY:\n")
            f.write(f"{body}\n\n")
            f.write("-" * 80 + "\n\n")
    
    # Print results
    print("\nTop 5 Most Suspicious Fraud-Related Emails:")
    for i, (_, email) in enumerate(final_top_emails.iterrows(), 1):
        print(f"\n{i}. From: {email['From'] or 'Unknown'} | Date: {email['Date'] or 'Unknown'}")
        print(f"   Subject: {email['Subject'] or 'No Subject'}")
        print(f"   Fraud Score: {email['FraudScore']:.1f}")
        
        # Extract and print a snippet
        body = email['Body']
        if body and isinstance(body, str):
            # Try to extract the most relevant part containing fraud keywords
            for keyword in ['LJM', 'Raptor', 'SPE', 'mark-to-market', 'off-balance']:
                if keyword.lower() in body.lower():
                    start = max(0, body.lower().find(keyword.lower()) - 50)
                    end = min(len(body), body.lower().find(keyword.lower()) + 150)
                    snippet = "..." + body[start:end] + "..."
                    print(f"   Relevant Snippet: {snippet}")
                    break
            else:
                # If no keyword found, just show the beginning
                snippet = body[:200] + "..." if len(body) > 200 else body
                print(f"   Snippet: {snippet}")
    
    print("\nAnalysis complete! Results saved to:")
    print("  - top_fraud_emails.csv (Raw data)")
    print("  - fraud_email_analysis.txt (Detailed analysis)")
    print("\nThese emails provide evidence of Enron's financial fraud through discussions")
    print("of SPEs, accounting manipulation, and suspicious executive communications.")

if __name__ == "__main__":
    main()