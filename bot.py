from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import random
import asyncio


start_keyboard = [['Sí', 'No']]
derivadas_keyboard = [['Potencia', 'Raíz'], ['Constante por función', 'Producto'], ['Modo Examen']]

start_markup = ReplyKeyboardMarkup(start_keyboard, one_time_keyboard=True)
derivadas_markup = ReplyKeyboardMarkup(derivadas_keyboard, one_time_keyboard=True)


ejercicios = {
    'Potencia': [
        {
            'ejercicio': '¿Cuál es la derivada de x^3?',
            'opciones': ['3x^2', 'x^2', '3x', '2x'],
            'respuesta': '3x^2'
        },
        {
            'ejercicio': '¿Cuál es la derivada de x^4?',
            'opciones': ['4x^3', '4x^2', '3x^4', '2x'],
            'respuesta': '4x^3'
        }
    ],
    'Raíz': [
        {
            'ejercicio': '¿Cuál es la derivada de √x?',
            'opciones': ['1/(2√x)', '√x', '2√x', '1/√x'],
            'respuesta': '1/(2√x)'
        }
    ]
}


def mezclar_opciones(opciones, respuesta):
    opciones_mezcladas = opciones[:]
    random.shuffle(opciones_mezcladas)
    return opciones_mezcladas


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('¡Hola! ¿Te gustaría practicar derivadas?', reply_markup=start_markup)


async def handle_start_response(update: Update, context: CallbackContext) -> None:
    if update.message.text == 'Sí':
        await update.message.reply_text('Genial, elige qué tipo de derivada quieres practicar:', reply_markup=derivadas_markup)
    else:
        await update.message.reply_text('Está bien, si cambias de opinión, solo házmelo saber.')


async def handle_derivada_choice(update: Update, context: CallbackContext) -> None:
    choice = update.message.text
    if choice in ejercicios:
        context.user_data['choice'] = choice
        context.user_data['modo'] = 'practica'
        ejercicio = ejercicios[choice][0]
        opciones_mezcladas = mezclar_opciones(ejercicio['opciones'], ejercicio['respuesta'])
        opciones_texto = "\n".join(f"{chr(97 + i)}. {opcion}" for i, opcion in enumerate(opciones_mezcladas))
        context.user_data['respuesta'] = f"{chr(97 + opciones_mezcladas.index(ejercicio['respuesta']))}. {ejercicio['respuesta']}"
        context.user_data['opciones_actuales'] = opciones_mezcladas
        context.user_data['ejercicios_restantes'] = ejercicios[choice][1:]
        await update.message.reply_text(f"{ejercicio['ejercicio']}\n\n{opciones_texto}")
    elif choice == 'Modo Examen':
        context.user_data['modo'] = 'examen'
        context.user_data['preguntas_examen'] = sum(ejercicios.values(), [])
        context.user_data['puntaje'] = 0
        context.user_data['total_preguntas'] = len(context.user_data['preguntas_examen'])
        await iniciar_examen(update, context)


async def iniciar_examen(update: Update, context: CallbackContext) -> None:
    if context.user_data['preguntas_examen']:
        pregunta = context.user_data['preguntas_examen'].pop(0)
        opciones_mezcladas = mezclar_opciones(pregunta['opciones'], pregunta['respuesta'])
        opciones_texto = "\n".join(f"{chr(97 + i)}. {opcion}" for i, opcion in enumerate(opciones_mezcladas))
        context.user_data['respuesta'] = f"{chr(97 + opciones_mezcladas.index(pregunta['respuesta']))}. {pregunta['respuesta']}"
        context.user_data['opciones_actuales'] = opciones_mezcladas
        await update.message.reply_text(f"{pregunta['ejercicio']}\n\n{opciones_texto}")
    else:
        await finalizar_examen(update, context)


async def finalizar_examen(update: Update, context: CallbackContext) -> None:
    puntaje = context.user_data.get('puntaje', 0)
    total = context.user_data.get('total_preguntas', 0)
    await update.message.reply_text(f'¡Has terminado el examen!\n\nTu puntaje final es: {puntaje}/{total}')
    context.user_data.clear()


async def handle_exercise_response(update: Update, context: CallbackContext) -> None:
    respuesta_correcta = context.user_data.get('respuesta')
    if respuesta_correcta:
        if update.message.text.strip().lower() == respuesta_correcta.strip().lower():
            await update.message.reply_text('¡Correcto!')
            if context.user_data.get('modo') == 'examen':
                context.user_data['puntaje'] += 1
        else:
            await update.message.reply_text(f'Incorrecto, la respuesta correcta es: {respuesta_correcta}')

        if context.user_data.get('modo') == 'practica' and context.user_data['ejercicios_restantes']:
            siguiente_ejercicio = context.user_data['ejercicios_restantes'].pop(0)
            opciones_mezcladas = mezclar_opciones(siguiente_ejercicio['opciones'], siguiente_ejercicio['respuesta'])
            context.user_data['respuesta'] = f"{chr(97 + opciones_mezcladas.index(siguiente_ejercicio['respuesta']))}. {siguiente_ejercicio['respuesta']}"
            context.user_data['opciones_actuales'] = opciones_mezcladas
            opciones_texto = "\n".join(f"{chr(97 + i)}. {opcion}" for i, opcion in enumerate(opciones_mezcladas))
            await update.message.reply_text(f"{siguiente_ejercicio['ejercicio']}\n\n{opciones_texto}")
        elif context.user_data.get('modo') == 'examen':
            await iniciar_examen(update, context)
        else:
            await update.message.reply_text('¡Has completado todos los ejercicios para esta derivada!')
            context.user_data.clear()
    else:
        await update.message.reply_text('Por favor, responde copiando la opción completa, por ejemplo: "c. 5x^4".')


def main():
    
    application = Application.builder().token("7552173818:AAFHTKHcMjFfPR-M-sRwzb_zRv_uLDJpoUI").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex('^(Sí|No)$'), handle_start_response))
    application.add_handler(MessageHandler(filters.Regex('^(Potencia|Raíz|Constante por función|Producto|Modo Examen)$'), handle_derivada_choice))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_exercise_response))

    loop = asyncio.get_event_loop()
    loop.run_until_complete(application.run_polling())

if __name__ == '__main__':
    main()
