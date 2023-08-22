import asyncio
import imaplib
import email
from email.header import decode_header
import re

from discord_webhook import DiscordWebhook, DiscordEmbed
import requests

from secret import EMAIL_ADDRESS, PASSWORD, DISCORD_WEBHOOK_URL

class PropertyInfo():
    def __init__(self, main_url, image_url, title, address, zipcode, location, roomcount, price):
        self.main_url = main_url
        self.image_url = image_url
        self.title = title
        self.address = address
        self.zipcode = zipcode
        self.location = location
        self.roomcount = roomcount
        self.price = price
    
    def create_address_string(self):
        address = f"{self.address}, {self.zipcode} {self.location}"
        return address

def create_embed(info):
    embed = DiscordEmbed(title=info.title, description=info.create_address_string())
    embed.set_author(name="Neues Suchergebnis", url=info.main_url)
    embed.set_thumbnail(url='attachment://img.jpg')
    embed.set_image(url='attachment://img.jpg')
    embed.add_embed_field(name="Preis", value=info.price)
    embed.add_embed_field(name="Zimmer", value=info.roomcount)
    embed.set_timestamp()

    return embed


def process_mailcontent(mailcontent):
    mailcontent = mailcontent.split("<!-- BLOCK START: object results -->")[1].split("<!-- BLOCK END: object results -->")[0]

    # Extract URLs using regular expression
    url_pattern = r'<ahref="([^"]+)">'

    # Extract image URL
    image_url = re.findall('<img src="([^"]+)"', mailcontent)[0]
    img_size = image_url.split(".ch/?")[1].split("/0/")[0]
    image_url = image_url.replace(img_size, "2000x2000")

    # Extract main URL
    main_url = re.findall('<ahref="([^"]+)\?utm_source', mailcontent)[0]

    # Extract property title using regular expression
    title_pattern = r'<ahref="[^"]+"style="text-decoration:none; color:#0066cc;">(.*?)</a>'
    title = re.findall(title_pattern, mailcontent)[0]

    # Extract address using regular expression
    address_pattern = r'<ahref="#" style="text-decoration:none; color:#333;">(.*?)<BR />(\d+)<text>&nbsp;</text>(.*?)</a>'
    address_match = re.search(address_pattern, mailcontent)
    address = address_match.group(1)
    zipcode = address_match.group(2)
    location = address_match.group(3)

    # Extract room count
    room_pattern = r'(\d+,\d+)&nbsp;Zimmer'
    room_count = re.search(room_pattern, mailcontent).group(1)

    # Extract price
    price_pattern = r'CHF [^"]+—'
    price = re.findall(price_pattern, mailcontent)[0]

    # Print the extracted information
    print("Main URL:", main_url)
    print("Image URL:", image_url)
    print("Title:", title)
    print("Address:", address)
    print("Zipcode:", zipcode)
    print("Location:", location)
    print("Room Count:", room_count)
    print("Price:", price)

    return PropertyInfo(main_url, image_url, title, address, zipcode, location, room_count, price)

# Define the function to be executed when a new email is received
def on_new_email(email_data):
    msg = email.message_from_bytes(email_data)
    subject, _ = decode_header(msg["Subject"])[0]
    sender, _ = decode_header(msg.get("From"))[0]
    
    print("New email received:")
    print("Subject:", subject)
    print("Sender:", sender)
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get('Content-Disposition'))

            # skip any text/plain (txt) attachments
            if ctype == 'text/plain' and 'attachment' not in cdispo:
                body = part.get_payload(decode=True).decode("utf-8").replace("\r", "").replace("\n", "").replace("\t", "")
                break
    # not multipart - i.e. plain text, no attachments, keeping fingers crossed
    else:
        body = msg.get_payload(decode=True).decode("utf-8").replace("\r", "").replace("\n", "").replace("\t", "")
    info = process_mailcontent(body)
    embed = create_embed(info)
    webhook = DiscordWebhook(url=DISCORD_WEBHOOK_URL)
    img_data = requests.get(info.image_url).content
    webhook.add_file(file=img_data, filename='img.jpg')
    webhook.add_embed(embed)
    response = webhook.execute()
    print("=" * 50)

# Asynchronous function to check for new emails
async def check_emails():
    while True:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_ADDRESS, PASSWORD)
        mail.select('immoscout')

        status, email_ids = mail.search(None, '(UNSEEN)')
        email_id_list = email_ids[0].split()

        for email_id in email_id_list:
            status, email_data = mail.fetch(email_id, "(RFC822)")
            if status == "OK":
                on_new_email(email_data[0][1])
                # Mark the email as seen
                mail.store(email_id, '+FLAGS', '\Seen')
        
        await asyncio.sleep(10)  # Check every 60 seconds

        # Logout and close the connection periodically to refresh the connection
        mail.logout()

# Run the event loop
if __name__ == "__main__":
    asyncio.run(check_emails())