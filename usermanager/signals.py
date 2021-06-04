from django.dispatch import receiver, Signal
from django_rest_passwordreset.signals import reset_password_token_created

from usermanager.models import ConfirmEmailToken, User
from api_diplom_final.celery import send_email


new_user_registered = Signal(
    providing_args=['user_id'],
)

new_order = Signal(
    providing_args=['user_id'],
)


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, **kwargs):
    """
    Отправка письма с токеном для сброса пароля.
    When a token is created, an e-mail needs to be sent to the user
    :param sender: View Class that sent the signal
    :param instance: View Instance that sent the signal
    :param reset_password_token: Token Model Object
    """

    title = f'Сброс пароля пользователя: {reset_password_token.user}'
    message = f'Токен: {reset_password_token.key}'
    email = reset_password_token.user
    send_email(title, message, email)


@receiver(new_user_registered)
def new_user_registered_signal(user_id, **kwargs):
    """ Отправка письмо с подтверждением почты. """
    token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user_id)
    title = f'Подтверждение регистрации пользователя: {token.user.email}'
    message = f'Токен: {token.key}'
    email = token.user.email
    send_email(title, message, email)


@receiver(new_order)
def new_order_signal(user_id, **kwargs):
    """
    Отправка письма при изменении статуса заказа.
    """
    user = User.objects.get(id=user_id)
    title = 'Уведомление о смене статуса заказа'
    message = 'Заказ сформирован.'
    email = user.email
    send_email.apply_async((title, message, email), countdown=5 * 60)
