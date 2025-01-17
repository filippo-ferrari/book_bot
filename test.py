import configparser    #this will be needed on final release to parse the id hash and token from a config.ini file
from telethon import TelegramClient, events, Button
import sqlite3
from datetime import datetime
from config import API_ID, API_HASH, BOT_TOKEN, session_name


print("Initializing configurations...")

# Start the bot session
client = TelegramClient(session_name, API_ID, API_HASH).start(bot_token=BOT_TOKEN)

######
###### START COMMAND
######

@client.on(events.NewMessage(pattern="(?i)/start"))
async def start(event):
    # Get the sender of the message
    sender = await event.get_sender()
    SENDER = sender.id
    text = "Benvenuto nel bot di compravendita di libri usati\nPer aggiungere un libro in vendita utilizza il comando /insert seguito da NOME, AUTORE, PREZZO, STATO, CITTA'.\nESEMPIO: /instert la Bibbia, Gesu' Cristo, 15.99 euro, come nuovo, Gerusalemme"
    text2 = "Per cercare un libro puoi usare /searchbyname seguito dal nome del libro o /searchbyauthor seguito dal nome dell'autore\nESEMPIO: /searchbyname la Bibbia\nESEMPIO: /searchbyauthor Gesu' Cristo"
    text3 = "Per vedere la lista dei tuoi libri messi in vendita usa /showmybooks e per cancellare un libro dalla lista usa /delete seguito dall'id numerico del libro.\nESEMPIO: /delete 33"

    await client.send_message(SENDER, text, parse_mode='html')
    await client.send_message(SENDER,text2, parse_mode='html')
    await client.send_message(SENDER,text3, parse_mode='html')

######
###### INSERT COMMAND
######

# Insert command
@client.on(events.NewMessage(pattern="(?i)/insert"))
async def insert(event):
    try:
        # Get the sender of the message
        sender = await event.get_sender()
        SENDER = sender.id

       # Get the text of the user AFTER the /insert command and split it into a list using the first space as the separator
        message_text = event.message.text.strip()
        command_parts = message_text.split(" ", 1)
        if len(command_parts) < 2:
            raise ValueError("Invalid command format")
        
        # Get the book details by splitting the remaining message using commas as the separator
        book_parts = command_parts[1].split(",")
        if len(book_parts) != 5:
            raise ValueError("Formato del libro non valido, riprova: (/instert TITOLO, AUTORE, PREZZO, STATO, CITTA')")
        book_name = book_parts[0].strip()
        book_author = book_parts[1].strip()
        book_price = book_parts[2].strip()
        book_status = book_parts[3].strip()
        book_location = book_parts[4].strip()
        dt_string = datetime.now().strftime("%d/%m/%Y") # Use the datetime library to the get the date (DAY/MONTH/YEAR)


        # Create the tuple "params" with all the parameters inserted by the user
        params = (book_name, book_author, book_price, book_status, book_location, SENDER, dt_string)
        sql_command = "INSERT INTO orders VALUES (NULL, ?, ?, ?, ?, ?, ?, ?);" # the initial NULL is for the AUTOINCREMENT id in the database
        crsr.execute(sql_command, params) # Execute the query
        conn.commit() # commit the changes

        # If at least 1 row is affected by the query we send specific messages
        if crsr.rowcount < 1:
            text = "Qualcosa e' andato storto, perfavore riprova"
            await client.send_message(SENDER, text, parse_mode='html')
        else:
            text = "Libro inserito correttamente"
            await client.send_message(SENDER, text, parse_mode='html')


    except Exception as e:
        print(e)
        await client.send_message(SENDER, "<b>Conversation Terminated✔</b>", parse_mode='html')
        return


######
###### SHOWMYBOOKS COMMAND
######

# Function that creates a message that contains a list of books
def create_message_select_query(ans):
    text = ""
    for i in ans:
        id = i[0]
        book_name = i[1]
        book_author = i[2]
        book_price = i[3]
        book_status = i[4]
        book_location = i[5]
        sender = i[6]
        creation_date = i[7]
        text += "<b>" + str(id) +"</b> | " + "<b>"+ str(book_name) +"</b> | " + "<b>"+ str(book_author) +"</b> | " + "<b>"+ str(book_price)+"</b> | " + "<b>"+ str(book_status)+"</b> |  " + "<b>"+ str(book_location)+"</b> | " + "<b>"+ str(creation_date)+"</b>\n\n"
    message = "<b>📖 I tuoi libri in vendita: 📖 </b>\n\n"+text
    return message



@client.on(events.NewMessage(pattern="(?i)/showmybooks"))
async def select(event):
    try:
        # Get the sender of the message
        sender = await event.get_sender()
        SENDER = sender.id
        # Execute the query and get all (*) the oders
        crsr.execute("SELECT * FROM orders WHERE SENDER = ?", (SENDER,)) # Make sure the query is ONLY for books of a specific user
        res = crsr.fetchall() # fetch all the results

        # If there is at least 1 row selected, print a message with the list of all the oders
        # The message is created using the function defined above
        if(res):
            testo_messaggio = create_message_select_query(res)
            await client.send_message(SENDER, testo_messaggio, parse_mode='html')
        # Otherwhise, print a default text
        else:
            text = "Non hai libri in vendita al momento."
            await client.send_message(event.chat_id, testo_messaggio, parse_mode='html')

    except Exception as e:
        print(e)
        await client.send_message(SENDER, "<b>Conversation Terminated✔</b>", parse_mode='html')
        return
    

######
###### DELETE COMMAND
######

@client.on(events.NewMessage(pattern="(?i)/delete"))
async def delete(event):
    try:
        # Get the sender
        sender = await event.get_sender()
        SENDER = sender.id

        # get list of words inserted by the user
        list_of_words = event.message.text.split(" ")
        id = list_of_words[1] # The second (1) element is the id

        # Crete the DELETE query passing the is as a parameter
        sql_command = "DELETE FROM orders WHERE id = (?) AND SENDER = (?);"
        ans = crsr.execute(sql_command, (id, SENDER,))
        conn.commit()
        
        # If at least 1 row is affected by the query we send a specific message
        if ans.rowcount < 1:
            text = "Impossibile cancellare il libro con l'ID {}, in quanto non esiste o non ti appartiene".format(id)
            await client.send_message(SENDER, text, parse_mode='html')
        else:
            text = "Il tuo libro con ID {} e' stato cancellato".format(id)
            await client.send_message(SENDER, text, parse_mode='html')

    except Exception as e: 
        print(e)
        await client.send_message(SENDER, "<b>Conversation Terminated✔️</b>", parse_mode='html')
        return


######
###### SEARCH BY NAME COMMAND
######

#create a function that searches a book by name
def search_book_by_name(book_name):
    sql_command = "SELECT * FROM orders WHERE name = ?;"
    crsr.execute(sql_command, (book_name,))
    rows = crsr.fetchall
    return rows


@client.on(events.NewMessage(pattern="^/searchbyname"))
async def search_by_name(event):
    try:
        # Get the sender
        sender = await event.get_sender()
        SENDER = sender.id

        # get list of words inserted by the user
        list_of_words = event.message.text.split(" ")
        book_name = " ".join(list_of_words[1:])  # Join all the words from the list except the command name

        # Create the SELECT query
        sql_command = "SELECT * FROM orders WHERE LOWER(book_name) LIKE LOWER('%{}%')".format(book_name)

        # Execute the query
        crsr.execute(sql_command)
        result = crsr.fetchall()

        # If no result is found, we send a message to inform the user
        if not result:
            text = "Nessun libro trovato dal titolo '{}'.".format(book_name)
            await client.send_message(SENDER, text, parse_mode='html')
        else:
            # Build the message to send to the user with all the books information
            text = "Libri dal titolo '{}' trovati:\n".format(book_name)
            for row in result:
                text += "BOOK ID: {}\nName: {}\nAuthor: {}\nPrice: {}\nStatus: {}\nLocation: {}\nDate of upload: {}\n\n".format(row[0],row[1], row[2], row[3], row[4], row[5], row[7])

            await client.send_message(SENDER, text, parse_mode='html')

    except Exception as e: 
        print(e)
        await client.send_message(SENDER, "<b>Conversation Terminated✔️</b>", parse_mode='html')
        return


######
###### SEARCH BY AUTHOR COMMAND
######

@client.on(events.NewMessage(pattern="^/searchbyauthor"))
async def search_by_name(event):
    try:
        # Get the sender
        sender = await event.get_sender()
        SENDER = sender.id

        # get list of words inserted by the user
        list_of_words = event.message.text.split(" ")
        book_author = " ".join(list_of_words[1:])  # Join all the words from the list except the command name

        # Create the SELECT query
        sql_command = "SELECT * FROM orders WHERE LOWER(book_author) LIKE LOWER('%{}%')".format(book_author)
        # Execute the query
        crsr.execute(sql_command)
        result = crsr.fetchall()

        # If no result is found, we send a message to inform the user
        if not result:
            text = "Nessun libro trovato dell'autore '{}'.".format(book_author)
            await client.send_message(SENDER, text, parse_mode='html')
        else:
            # Build the message to send to the user with all the books information
            text = "Libri dell'autore '{}' trovati:\n".format(book_author)
            for row in result:
                text += "BOOK ID: {}\nName: {}\nAuthor: {}\nPrice: {}\nStatus: {}\nLocation: {}\nDate of upload: {}\n\n".format(row[0],row[1], row[2], row[3], row[4], row[5], row[7])

            await client.send_message(SENDER, text, parse_mode='html')

    except Exception as e: 
        print(e)
        await client.send_message(SENDER, "<b>Conversation Terminated✔️</b>", parse_mode='html')
        return
    
######
###### BUY THIS BOOK COMMAND
######

@client.on(events.NewMessage(pattern="(?i)/buythisbook"))
async def select(event):
    try:
        ## Get the sender
        sender = await event.get_sender()
        buyer_id = sender.id
        #buyer_hash = await client.get_input_entity(buyer_id)    DO I EVEN?

        # get list of words inserted by the user
        list_of_words = event.message.text.split(" ")
        id = list_of_words[1] # The second (1) element is the id

        # Execute the query and get all (*) the oders
        crsr.execute("SELECT * FROM orders WHERE id = ?", (id,)) 
        res = crsr.fetchall()
        
        if not res:
            text = "Nessun libro presente con questo ID, ricontrolla perfavore.\nUsa l'ID del libro (esempio: /buythisbook *BOOK ID*)"
            await client.send_message(buyer_id, text, parse_mode='html')
            return
        

        else:
            seller_id = res[0][6]
            print('FETCH SUCCESSFUL, BOOK RETRIEVED') #testing only remove afterwards
            print("Interest in a book has been shown by user", buyer_id, "to a book from user", seller_id)
            # fetch user objects for buyer and seller
            buyer = await client.get_entity(int(buyer_id))
            seller = await client.get_entity(int(seller_id))
            book_info_seller = f"Un utente e interessato ad un tuo libro.\n\nID del libro: {res[0][0]}\nBook Title: {res[0][1]}\nAuthor: {res[0][2]}\nPrice: {res[0][3]}\nStatus: {res[0][4]}\nLocation: {res[0][5]}\nDate: {res[0][7]}\n\nContatta l'utente:\nNome: {buyer.first_name}\nCognome: {buyer.last_name}\nUsername: {buyer.username}\n\n Ricorda di cancellare il libro una volta venduto (/delete *BOOK ID*)"    #LINK: https://t.me/{buyer.username}
            book_info_buyer = f"Abbiamo notificato il venditore del tuo interesse per un suo libro.\nDi seguito trovi i dati del libro\n\nBook Title: {res[0][1]}\nAuthor: {res[0][2]}\nPrice: {res[0][3]}\nStatus: {res[0][4]}\nLocation: {res[0][5]}\nDate: {res[0][7]}\n\nRicordati di chiedere tutte le informazioni che ritieni necessarie al venditore (tipologia di spedizione, consegna a mano, foto del libro etc.)\n\nInfo sul venditore:\nNome: {seller.first_name}\nCognome: {seller.last_name}\nUsername: {seller.username}"
            
            button_seller = Button.url('Contatta il compratore', url=f"https://t.me/{buyer.username}")
            button_buyer = Button.url('Contatta il venditore', url=f"https://t.me/{seller.username}")
            
            message_to_seller = await client.send_message(int(seller_id), book_info_seller, buttons=[button_seller])
            await client.pin_message(int(seller_id), message_to_seller, notify=True)
            message_to_buyer = await client.send_message(int(buyer_id), book_info_buyer, buttons=[button_buyer])
            await client.pin_message(int(buyer_id), message_to_buyer, notify=True)

    except Exception as e:
        print(e)
        await client.send_message(buyer_id, "<b>Conversation Terminated✔</b>", parse_mode='html')
        return


########################################################################################################
######################################################################################################## MAIN
if __name__ == '__main__':
    try:
        print("Initializing Database...")
        # Connect to local database
        db_name = '/home/filippoferrari/Documents/book_test/test-database.db' # Insert the database name.
        conn = sqlite3.connect(db_name, check_same_thread=False)
        # Create the cursor
        # The cursor is an instance using which you can invoke methods that execute SQLite statements, fetch data from the result sets of the queries.
        crsr = conn.cursor()
        print("Connected to the database")

        # Command that creates the "oders" table 
        sql_command = """CREATE TABLE IF NOT EXISTS orders ( 
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            book_name VARCHAR(300),
            book_author VARCHAR(300), 
            book_price VARCHAR(100),
            book_status VARCHAR(200),
            book_location VARCHAR(200),
            SENDER VARCHAR(300),
            LAST_EDIT VARCHAR(100));"""
        crsr.execute(sql_command)
        print("All tables are ready")

        print("Bot Started")
        client.run_until_disconnected()

    except Exception as error:
        print('Cause: {}'.format(error))

                                                                                                                                                                                                                                                                                                                                                                                                
