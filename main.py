import re
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)
from variables import TOKEN
from optimal_fun import find_solutions, snack, ridotto, intero

WAITING_FOR_CREDITO = 1
MAX_CREDITO = 500


def escape_markdown(text):
    return re.sub(r'([_\[\]\(\)\~\>\#\+\-\=\|\{\}\.\!])', r'\\\1', text)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Ciao! Mandami il credito della tua tessera della mensa (es. 0.3)")
    return WAITING_FOR_CREDITO


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Canceled. Usa /start per ricominciare.")
    return ConversationHandler.END


async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    ## Validazione input
    credito_str = update.message.text.replace(",", ".").strip()
    credito = float(credito_str)

    if credito != round(credito, 1):
        await update.message.reply_text("Non è possibile, solo la prima cifra decimale può essere diversa da 0")
        return WAITING_FOR_CREDITO

    
    if credito < 0:
        await update.message.reply_text("Il credito non può essere negativo")
        return WAITING_FOR_CREDITO

    if credito == 0:
        await update.message.reply_text("WOW, hai la tessera esattamente a 0. Abbandona la mensa o passa al borsellino elettronico.")
        return WAITING_FOR_CREDITO

    if credito > MAX_CREDITO:
        await update.message.reply_text("Are you Elon Musk? Metti un credito più basso per favore...")
        return WAITING_FOR_CREDITO


    ## Calcolo soluzioni
    solutions = find_solutions(credito)


    ## Preparo la tabella
    header = f"{'pasti':>5} {'snack':>5} {'ridotto':>7} {'intero':>6} {'ricarica':>8}"
    rows = [
            f"{total:>5} {a:>5} {b:>7} {c:>6} {ricarica:>7}€"
        for a, b, c, total, ricarica in solutions
    ]
    table = "\n".join([header] + rows)

    message = f"🍽 *Possibili combinazioni di pasti:*\n```\n{table}\n```"
    message = escape_markdown(message)

    ## Mando la tabella in markdown
    await update.message.reply_markdown_v2(message, reply_markup=ReplyKeyboardRemove())

    return WAITING_FOR_CREDITO


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_FOR_CREDITO: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()


if __name__ == "__main__":
    main()

