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
    
    img_tag = soup.find('img', alt=linkElementText) # search by img text
    if img_tag:
        parent_a_tag = img_tag.find_parent('a')
        if parent_a_tag:
            return parent_a_tag.get('href')
    
    link_tag = soup.find('a', string=linkElementText) # search by text
    if link_tag:
        return link_tag.get('href')
    
    tqdm.write(f"No image or link found with alt/text: {linkElementText}") #this is bad
    return None

# Main function
def process_mailbox(mail):
    mail.select('inbox')
    
    search_criteria = '(SUBJECT "{}")'.format(gmailConfig["emailTitle"])
    typ, data = mail.search(None, search_criteria)
    if typ == 'OK':
        emails = data[0].split()
        total_emails = len(emails)
        print('found {} emails with subject containing "{}"'.format(total_emails, gmailConfig["emailTitle"]))

        file_name = f'{gmailConfig["emailTitle"].replace(" ", "_")}_links.txt' # filename based on email title

        with tqdm(total=total_emails, desc="Processing emails", unit="email") as pbar:
            for idx, num in enumerate(emails):
                typ, data = mail.fetch(num, '(RFC822)')
                if typ == 'OK':
                    email_message = email.message_from_bytes(data[0][1])
                    if email_message.is_multipart():
                        for part in email_message.walk():
                            if part.get_content_type() == 'text/html':
                                body = part.get_payload(decode=True)
                                link = find_link(body, gmailConfig['linkElementText'])
                                if link:
                                    with open(file_name, 'a') as file:
                                        file.write(link + '\n')
                                break

                pbar.update(1) #update progress bar

        totalLinks = sum(1 for line in open(file_name))
        print(f"\n{totalLinks} Links have been written to {file_name}")

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
