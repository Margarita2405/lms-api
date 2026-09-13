import stripe
from django.conf import settings

# Устанавливаем секретный ключ Stripe (берём из settings)
stripe.api_key = settings.STRIPE_API_KEY


def create_stripe_product(course):
    """Создаёт продукт в Stripe на основе объекта курса."""
    product = stripe.Product.create(
        name=course.title,
        description=course.description or "",
    )
    return product.id  # возвращаем ID созданного продукта


def create_stripe_price(product_id, amount):
    """Создаёт цену в Stripe. amount — сумма в рублях (Decimal). Переводим в копейки (умножаем на 100)."""
    price = stripe.Price.create(
        unit_amount=int(amount * 100),  # перевод в копейки
        currency="rub",
        product=product_id,
    )
    return price.id


def create_checkout_session(price_id, success_url, cancel_url):
    """Создаёт сессию оплаты и возвращает её ID и URL для перенаправления."""
    session = stripe.checkout.Session.create(
        success_url=success_url,
        cancel_url=cancel_url,
        payment_method_types=["card"],
        line_items=[
            {
                "price": price_id,
                "quantity": 1,
            }
        ],
        mode="payment",
    )
    return session.id, session.url


def retrieve_session_status(session_id):
    """Получает статус оплаты по ID сессии (для дополнительного задания)."""
    session = stripe.checkout.Session.retrieve(session_id)
    return session.payment_status  # 'paid' или 'unpaid'
