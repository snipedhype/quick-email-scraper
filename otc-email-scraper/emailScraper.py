import imaplib
import email
from bs4 import BeautifulSoup
from tqdm import tqdm  

def load_config(file_path='config.txt'):
    config = {}
    with open(file_path, 'r') as file:
        for line in file:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                config[key.strip()] = value.strip()
    return config

config = load_config()

gmailConfig = { # config for imap
    'user': config['user'],
    'password': config['password'],
    'host': config['host'],
    'port': config['port'],
    'tls': True,  # must be true idk why
    'emailTitle': config['emailTitle'],
    'linkElementText': config['linkElementText']
}

def find_link(body, linkElementText):
    soup = BeautifulSoup(body, 'html.parser')
    
    # Search for image by alt text
    img_tag = soup.find('img', alt=linkElementText)
    if img_tag:
        parent_a_tag = img_tag.find_parent('a')
        if parent_a_tag:
            return parent_a_tag.get('href')
    
    # Search for link by text
    link_tag = soup.find('a', string=linkElementText)
    if link_tag:
        return link_tag.get('href')
    
    tqdm.write(f"No image or link found with alt/text: {linkElementText}")
    return None

# Main function
def process_mailbox(mail):
    mail.select('inbox') # folder
    
    search_criteria = '(SUBJECT "{}")'.format(gmailConfig["emailTitle"])
    typ, data = mail.search(None, search_criteria)
    if typ == 'OK':
        emails = data[0].split()
        total_emails = len(emails)
        print(f'Found {total_emails} emails with subject containing "{gmailConfig["emailTitle"]}"')

        file_name = f'{gmailConfig["emailTitle"].replace(" ", "_")}_links.txt'  # Filename based on email title

        with tqdm(total=total_emails, desc="Processing emails", unit="email") as pbar:
            for idx, num in enumerate(emails):
                typ, data = mail.fetch(num, '(RFC822)')
                if typ == 'OK':
                    email_message = email.message_from_bytes(data[0][1])
                    email_subject = email_message.get('subject')
                    #print(f'Processing email {idx+1}/{total_emails}: {email_subject}')

                    # Check if the email is multipart
                    if email_message.is_multipart():
                        for part in email_message.walk():
                            if part.get_content_type() == 'text/html':  # Look for HTML parts
                                body = part.get_payload(decode=True)
                                link = find_link(body, gmailConfig['linkElementText'])
                                if link:
                                    with open(file_name, 'a') as file:
                                        file.write(link + '\n')
                                    #print(f"Link found and saved: {link}")
                                break
                    else:
                        # For non-multipart emails, handle the main payload
                        payload = email_message.get_payload(decode=True)
                        if payload:
                            link = find_link(payload, gmailConfig['linkElementText'])
                            if link:
                                with open(file_name, 'a') as file:
                                    file.write(link + '\n')
                                #print(f"Link found and saved: {link}")

                pbar.update(1)  #update the progress bar

        total_links = sum(1 for line in open(file_name))
        print(f"\n{total_links} Links have been written to {file_name}")

try:
    mail = imaplib.IMAP4_SSL(gmailConfig['host'])
    mail.login(gmailConfig['user'], gmailConfig['password'])
    process_mailbox(mail)
except imaplib.IMAP4.error as e:
    print(f'IMAP error: {e}')
finally:
    try:
        mail.logout()
    except:
        pass