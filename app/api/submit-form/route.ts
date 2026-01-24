import { NextRequest, NextResponse } from 'next/server'

interface FormData {
  name: string
  email: string
  phone: string
  occasion: string
  videoCount: string
  message: string
}

const occasionLabels: Record<string, string> = {
  wedding: '💒 Весілля',
  birthday: '🎂 День народження',
  anniversary: '🎉 Ювілей',
  corporate: '🏢 Корпоратив',
  other: '📋 Інше'
}

export async function POST(request: NextRequest) {
  try {
    const formData: FormData = await request.json()

    // Validate required fields
    if (!formData.name || !formData.phone || !formData.occasion) {
      return NextResponse.json(
        { error: 'Будь ласка, заповніть всі обов\'язкові поля' },
        { status: 400 }
      )
    }

    // Get Telegram credentials from environment variables
    const botToken = process.env.TELEGRAM_BOT_TOKEN
    const chatId = process.env.TELEGRAM_CHAT_ID

    if (!botToken || !chatId) {
      console.error('Telegram credentials not configured')
      return NextResponse.json(
        { error: 'Помилка конфігурації сервера. Спробуйте пізніше.' },
        { status: 500 }
      )
    }

    // Format the message for Telegram
    const occasionLabel = occasionLabels[formData.occasion] || formData.occasion
    
    const message = `
🎬 *НОВА ЗАЯВКА НА ВІДЕО*

👤 *Ім'я:* ${escapeMarkdown(formData.name)}
📱 *Телефон:* ${escapeMarkdown(formData.phone)}
📧 *Email:* ${formData.email ? escapeMarkdown(formData.email) : '_не вказано_'}

📅 *Тип події:* ${occasionLabel}
🎥 *Кількість відео:* ${escapeMarkdown(formData.videoCount)}

${formData.message ? `💬 *Додаткова інформація:*\n${escapeMarkdown(formData.message)}` : ''}

━━━━━━━━━━━━━━━━━━
📆 Дата: ${new Date().toLocaleString('uk-UA', { timeZone: 'Europe/Kyiv' })}
    `.trim()

    // Send message to Telegram
    const telegramUrl = `https://api.telegram.org/bot${botToken}/sendMessage`
    
    const telegramResponse = await fetch(telegramUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        chat_id: chatId,
        text: message,
        parse_mode: 'Markdown',
      }),
    })

    const telegramResult = await telegramResponse.json()

    if (!telegramResponse.ok) {
      console.error('Telegram API error:', telegramResult)
      return NextResponse.json(
        { error: 'Помилка відправки повідомлення. Спробуйте пізніше.' },
        { status: 500 }
      )
    }

    return NextResponse.json({ 
      success: true, 
      message: 'Заявку успішно відправлено!' 
    })

  } catch (error) {
    console.error('Form submission error:', error)
    return NextResponse.json(
      { error: 'Виникла помилка. Спробуйте пізніше або зв\'яжіться з нами через Telegram.' },
      { status: 500 }
    )
  }
}

// Helper function to escape special Markdown characters
function escapeMarkdown(text: string): string {
  return text.replace(/[_*[\]()~`>#+=|{}.!-]/g, '\\$&')
}
