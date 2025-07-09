import re
import numpy as np
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler

from variables import TOKEN


def escape_markdown(text):
    return re.sub(r'([_\[\]\(\)\~\>\#\+\-\=\|\{\}\.\!])', r'\\\1', text)


snack = 3.10
ridotto = 4.40
intero = 4.90

prezzi = {'snack': snack, 'ridotto': ridotto, 'intero': intero}


def posso_caricare_multiplo_5(a, b, c, credito) -> bool:
    ## Prezzi menù

    speso = a * snack + b * ridotto + c * intero
    caricare = round(speso - credito, 2)

    return caricare % 5 == 0


def find_solutions(credito, preferito, offset, max_solutions = 10):

    pasti_possibili = np.zeros([max_solutions, 3], dtype=int)
    ii = 0

    S = 1  # minimal possible sum 

    # generate all (a,b,c) with a+b+c == S
    while S < 100 and ii < 10:
        for a in range(0, S + 1):
            for b in range(0, S - a + 1):
                c = S - a - b

                if posso_caricare_multiplo_5(a, b, c, credito):

                    pasti_possibili[ii, :] = (a, b, c) 
                    ii += 1

                    if ii == 10:
                        break
            if ii == 10:
                break

        S += 1
    
    if ii < max_solutions and ii > 0:
        return pasti_possibili[:ii, :]

    elif ii == 0:
        return 0

    else:
        if preferito == "snack":
            pasti_possibili[:, 0] += offset
        if preferito == "ridotto":
            pasti_possibili[:, 1] += offset
        if preferito == "intero":
            pasti_possibili[:, 2] += offset

        return pasti_possibili



ASK_CREDITO, ASK_PREFERENCE = range(2)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ciao! Mandami il credito della tua tessera della mensa (es. 0.3)"
    )
    return ASK_CREDITO

# Riceve il credito e chiede la preferenza
async def ask_preference(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(update.message.text.strip()) > 10:
            await update.message.reply_text("Messaggio troppo lungo!")
            return ASK_CREDITO

        credito_str = update.message.text.replace(",", ".").strip()
        credito = float(credito_str)

        if credito != round(credito, 1):
            await update.message.reply_text("Non è possibile, solo la prima cifra decimale può essere diversa da 0")
            return ASK_CREDITO

        if credito < 0:
            await update.message.reply_text("Il credito non può essere negativo")
            return ASK_CREDITO

        if credito == 0:
            await update.message.reply_text("WOW, hai la tessera esattamente a 0. Abbandona la mensa o passa al borsellino elettronico.")
            return ASK_CREDITO

        if credito > 363e9:
            await update.message.reply_text("Are you Elon Musk? Metti un credito più basso per favore...")
            return ASK_CREDITO

        context.user_data['credito'] = credito

        keyboard = [['snack', 'ridotto', 'intero']]
        await update.message.reply_text(
            "Cosa preferisci?",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        )
        return ASK_PREFERENCE

    except ValueError:
        await update.message.reply_text("Per favore, mandami solo un numero come credito (es. 0.3)")
        return ASK_CREDITO

# Riceve la preferenza e mostra soluzioni
async def show_solutions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    preferito = update.message.text.strip().lower()
    credito = context.user_data.get('credito')

    if preferito not in ['intero', 'ridotto', 'snack']:
        await update.message.reply_text("Per favore scegli solo tra: intero, ridotto o snack.")
        return ASK_PREFERENCE

    offset = int(credito // prezzi[preferito])
    credito_residuo = round(credito - offset * prezzi[preferito], 2)
    print(offset, credito_residuo)

    solutions = find_solutions(credito_residuo, preferito, offset)

    if len(solutions) == 0:
        await update.message.reply_text("Mi dispiace, non ho trovato nessuna combinazione valida.")
        return ConversationHandler.END

    totals = solutions.sum(axis=1)
    header = f"{'pasti':>5} {'snack':>5} {'ridotto':>7} {'intero':>6} {'ricarica':>8}"
    rows = [
            f"{total:>5} {a:>5} {b:>7} {c:>6} {int(a*snack + b*ridotto + c*intero - credito):>7}€"
        for total, (a,b,c) in zip(totals, solutions)
    ]
    table = "\n".join([header] + rows)

    message = f"🍽 *Possibili combinazioni di pasti (priorità: {preferito}):*\n```\n{table}\n```"
    message = escape_markdown(message)

    await update.message.reply_markdown_v2(message, reply_markup=ReplyKeyboardRemove())
    return ASK_CREDITO

# /cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Conversazione annullata.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# MAIN
def main():
    logging.basicConfig(level=logging.INFO)

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_CREDITO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_preference)
            ],
            ASK_PREFERENCE: [
                MessageHandler(filters.Regex(r'^(intero|ridotto|snack)$'), show_solutions),
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_preference)
            ],
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CommandHandler('start', start)  # aggiunto qui
        ]
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()

