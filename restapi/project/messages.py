from django.utils.translation import get_language


def get_message(key, flat=False):
    if key is None or len(str(key)) == 0:
        return {'detail': ''} if not flat else ''
    if get_language() == 'fa':
        return {'detail': MESSAGES[key]['fa']} if not flat else MESSAGES[key]['fa']
    return {'detail': MESSAGES[key]['en']} if not flat else MESSAGES[key]['en']


MESSAGES = {
    # Profile app
    'phone_wrong': {'fa': 'قالب شماره تلفن اشتباه است! شماره تلفن باید با 09 شروع شود.', 'en': 'Wrong phone number format! phone must start with 09.'},
    'name_wrong': {'fa': 'نام نامعتبر است! نام باید حداقل 3 حرف باشد.', 'en': 'Invalid name! name must have minimum length of 3 characters'},
    'channel_name_wrong': {'fa': 'نام کانال  نامعتبر است! نام کانال باید حداقل 3 حرف باشد یا باید خالی باشد.', 'en': 'Invalid channel name! name must have minimum length of 3 characters or must be None'},
    'user_exist': {'fa': 'این کاربر از قبل در سامانه وجود دارد!', 'en': 'This user instance is already exist!'},
    'user_not_exist': {'fa': 'چنین کاربری وجود ندارد.', 'en': 'There is no such a user.'},
    'login_406': {'fa': 'حداکثر نشست ها فعال می باشند!', 'en': 'Max active sessions!'},
    'contact_yourself_406': {'fa': 'نمی توانید حساب کاربری خود را به مخاطبینتان اضافه کنید.', 'en': 'Cant add yourself account to your contacts.'},
    'delete_contact_409': {'fa': 'هنگام اجرا عملیات خطایی رخ داد!', 'en': 'An error occurred while performing the operation!'},
    'sync_contact_406': {'fa': 'کاربر جدیدی برای افزودن به مخاطبین شما وجود ندارد!', 'en': 'There is no new user to add to your contacts!'},
    'channel_name_409': {'fa': 'این نام کانال از قبل انتخاب شده است!', 'en': 'This channel name was chosen before!'},
    'generate_code_423': {'fa': 'پیامک برای شما ارسال شده‌است، پس از انقضا آن دوباره امتحان کنید!', 'en': 'Message was sent for you, after it\'s expiration try again!'},
    'not_whitelist': {'fa': 'این کانال در لیست سفید پیدا نشد', 'en': 'This account is not in a whitelist!'},
    'no_live': {'fa': 'پخش‌زنده فعالی برای این کانال وجود ندارد!', 'en': 'There is no active live on this channel!'},
    'insta_not_available': {'fa': 'اینستاگرام پاسخ‌گو نمی‌باشد!', 'en': 'Instagram is not responsive!'},
    'create_contact_conflict': {'fa': 'شماره وارد شده از قبل در مخاطبین شما قرار دارد.', 'en': 'The entered number is already in your contacts.'},

    # Statuses
    208: {'fa': 'این درخواست قبلاً گزارش شده است!', 'en': 'This request was reported before!'},
    400: {'fa': 'درخواست نامناسب!', 'en': 'Bad request!'},
    403: {'fa': 'شما به این بخش دسترسی ندارید!', 'en': 'You dont have access to this section!'},
    404: {'fa': 'یافت نشد!', 'en': 'Not found!'},
    406: {'fa': 'این درخواست قابل قبول نیست!', 'en': 'Not acceptable!'},
    409: {'fa': 'درخواست شما با مشکل روبه رو شده!', 'en': 'Your request has conflict!'},
    422: {'fa': 'حجم فضای ذخیره‌سازی شما کافی نمی باشد!', 'en': 'Your storage space volume is not enough!'},
    503: {'fa': 'سامانه در دسترس نیست!', 'en': 'Service is unavailable!'},
}