from flask import Flask, request, redirect, jsonify, abort, render_template, make_response
from apscheduler.schedulers.background import BackgroundScheduler

import functools
from collections import Counter
import time
from nanoid import generate

from redis_om import Migrator
from redis_om.model import NotFoundError
from pydantic import ValidationError

from src.schema import Url, STATUS, NumOfDaysDeterminedAsDeactivated
from src.logger import initLogger
from src.constant import *
from src.utils import *
from src.swagger import initSwaggerUI

ROUTE_NAME = ('shorten', 'swagger', )

app = Flask(__name__)
initSwaggerUI(app)
logger = initLogger()
logger.handlers = logger.handlers
logger.setLevel(logger.level)

def logExecutionTime(func):
   @functools.wraps(func)
   def wrapper(*args, **kwargs):
      startTime = time.perf_counter()
      res = func(*args, **kwargs)
      endTime = time.perf_counter()
      output = '[{}] took {:.3f}s'.format(func.__name__, endTime - startTime)
      logger.info(output)
      return res
   return wrapper

@app.route('/')
@app.route('/shorten', methods=['GET'])
def index():
    return render_template('index.html')

def validateShortkey(shortKey):
    if len(shortKey) > ALIAS_URL_MAX_LENGTH:
        return f'Bad request: The character length of the alias cannot exceed {ALIAS_URL_MAX_LENGTH}.'
    elif len(shortKey) < ALIAS_URL_MIN_LENGTH:
        return f'Bad request: The character length of the alias cannot be less than {ALIAS_URL_MIN_LENGTH}.'
    if shortKey in ROUTE_NAME:
        return f'Bad request: the short key cannot be the same as route name.'
    try:
        validateCharacters(shortKey)
    except Exception as e:
        return f'Bad request: {e}'

def isShortkeyExist(shortKey):
    # check the short URL in use or not
    results = find_by_shortkey(shortKey)
    return len(results) > 0

@app.route('/api/service/admin/<user>', methods=['GET'])
def checkSystemAdmin(user):
    if user in ADMIN_USER_ID:
        return jsonify('ok')
    return abort(make_response(jsonify(message=f'User "{user}" is not admin.'), 400))

@app.route('/<shortKey>', methods=['GET'])
@logExecutionTime
def redirectUrl(shortKey):
    error = validateShortkey(shortKey)
    if error is not None:
        return abort(make_response(jsonify(message=error), 400))

    # Check if the response is already cached
    results = find_by_shortkey(shortKey)
    if len(results) == 0:
        shortUrl = SHORT_KEY_PREFIX + shortKey
        error = f'Not found original url by {shortUrl}'
        return abort(make_response(jsonify(message=error), 404))

    url = results[0]
    longUrl = url.original_url
    url.utilization = url.utilization + 1
    url.lastRedirectTime = datetime.datetime.utcnow()
    url.status = STATUS.USED.value
    url.save()
    logger.info(f'Redirect by short key {shortKey}.')
    return redirect(longUrl)

@app.route('/api/shorten', methods=['POST'])
@logExecutionTime
def shortenUrl():
    try:
        data = json.loads(request.data.decode())
        userId = data['user_id']
        originalUrl = data['original_url']
        shortKey = data['short_key']
        expireType = data['expire_type']
    except:
        return abort(make_response(jsonify(message='Bad request'), 400))

    # validate for long url
    try:
        validateUrl(originalUrl)
    except Exception as e:
        error = f'Bad request: {e}'
        return abort(make_response(jsonify(message=error), 400))
    
    # validate for short key
    if len(shortKey) > 0:
        error = validateShortkey(shortKey)
        if error is not None:
            return abort(make_response(jsonify(message=error), 400))
        if isShortkeyExist(shortKey):
            error = f'Bad request: The short key "{shortKey}" is in use.'
            return abort(make_response(jsonify(message=error), 400))

    # validate for expire type
    if expireType not in ('1month', '3month', '6month', '1year', 'indefinitely'):
        error = 'Bad request: invalid expire time'
        return abort(make_response(jsonify(message=error), 400))
    expireTime = type2date(expireType)

    try:
        shortUrl, urlId = generate_shorturl(userId, originalUrl, shortKey, expireTime)
        logger.info(f'Generate short url: {shortUrl}.')
        return jsonify(short_url=shortUrl, long_url=originalUrl, url_id=urlId)
    except ValidationError as e:
        error = 'Validation error: ' + str(e)
        logger.error(error)
        return abort(make_response(jsonify(message=error), 500))
    except Exception as e:
        error = 'Internal error: ' + str(e)
        logger.error(error)
        return abort(make_response(jsonify(message=error), 500))
   
@app.route('/api/url/<id>', methods=['GET'])
def findById(id):
    try:
        url = Url.get(id)
        result = url.dict()
        shortKey = result['short_key']
        result.update({'short_url': SHORT_KEY_PREFIX + shortKey})
        logger.info(f'Found short key {shortKey} by id: {id}.')
        return result
    except NotFoundError:
        error = 'Not found by url id: ' + id
        return abort(make_response(jsonify(message=error), 404))

@app.route('/api/url/<id>', methods=['DELETE'])
def deleteById(id):
    try:
        url = Url.get(id)
        url.status = STATUS.DELETED.value
        url.save()
        logger.info(f'Delete short url by id: {id}.')
        return jsonify('ok')
    except NotFoundError:
        error = 'Not found by url id: ' + id
        return abort(make_response(jsonify(message=error), 404))
    except ValidationError as e:
        error = 'Validation error: ' + str(e)
        logger.error(error)
        return abort(make_response(jsonify(message=error), 500))
    except Exception as e:
        error = 'Internal error: ' + str(e)
        logger.error(error)
        return abort(make_response(jsonify(message=error), 500))

@app.route('/api/url/<id>', methods=['POST'])
def updateById(id):
    try:
        data = json.loads(request.data.decode())
        originalUrl = data['original_url']
        validateUrl(originalUrl)
    except Exception as e:
        error = f'Bad request: {e}'
        return abort(make_response(jsonify(message=error), 400))
    try:
        url = Url.get(id)
        url.original_url = originalUrl
        url.hash_original = url2hash(originalUrl)
        url.save()
        shortUrl = SHORT_KEY_PREFIX + url.short_key
        logger.info(f'Update short url {shortUrl} by id: {id}.')
        return jsonify(short_url=shortUrl, long_url=url.original_url, url_id=url.pk)
    except NotFoundError:
        error = 'Not found by url id: ' + id
        return abort(make_response(jsonify(message=error), 404))
    except ValidationError as e:
        error = 'Validation error: ' + str(e)
        logger.error(error)
        return abort(make_response(jsonify(message=error), 500))
    except Exception as e:
        error = 'Internal error: ' + str(e)
        logger.error(error)
        return abort(make_response(jsonify(message=error), 500))
    
@app.route('/api/longurl', methods=['GET'])
def queryByLongurl():
    try:
        data = json.loads(request.data.decode())
        longUrl = data['original_url']
        if len(longUrl) == 0:
            return abort(400, f'Bad request: No long url specified.')
    except:
        return abort(make_response(jsonify(message='Bad request'), 400))

    hash_value = url2hash(longUrl)
    try:
        datas = Url.find(
            (Url.hash_original == hash_value)
        ).all()
    except NotFoundError:
        error = 'Not found by long url: ' + longUrl
        return abort(make_response(jsonify(message=error), 404))

    logger.debug(f'Hash value "{hash_value}" found {len(datas)} records')
    return build_results(datas)

@app.route('/api/longurl', methods=['POST'])
@logExecutionTime
def updateLongurlByShortkey():
    try:
        data = json.loads(request.data.decode())
        shortKey = data['short_key']
        originalUrl = data['original_url']
        # validate for short key
        error = validateShortkey(shortKey)
        if error is not None:
            return abort(make_response(jsonify(message=error), 400))
        urls = find_by_shortkey(shortKey)
        if len(urls) == 0:
            error = 'Not found by short key: ' + shortKey
            return abort(make_response(jsonify(message=error), 404))
        # validate for long url
        try:
            validateUrl(originalUrl)
        except Exception as e:
            error = f'Bad request: {e}'
            return abort(make_response(jsonify(message=error), 400))
    except:
        return abort(make_response(jsonify(message='Bad request'), 400))
    try:
        url = urls[0]
        url.original_url = originalUrl
        url.hash_original = url2hash(originalUrl)
        url.save()
        shortUrl = SHORT_KEY_PREFIX + url.short_key
        logger.info(f'The long url of "{shortUrl}" updated into {originalUrl}.')
        return jsonify(short_url=shortUrl, long_url=url.original_url, url_id=url.pk)
    except ValidationError as e:
        error = 'Validation error: ' + str(e)
        logger.error(error)
        return abort(make_response(jsonify(message=error), 500))
    except Exception as e:
        error = 'Internal error: ' + str(e)
        logger.error(error)
        return abort(make_response(jsonify(message=error), 500))

@app.route('/api/shortkey/<shortKey>', methods=['GET'])
def queryByShortkey(shortKey):
    # validate for short key
    error = validateShortkey(shortKey)
    if error is not None:
        return abort(make_response(jsonify(message=error), 400))
    urls = find_by_shortkey(shortKey)
    if len(urls) == 0:
        error = 'Not found by short key: ' + shortKey
        return abort(make_response(jsonify(message=error), 404))
    return build_results(urls)

@app.route('/api/status/<id>/<status>', methods=['POST'])
def updateStatusById(id, status):
    try:
        status = status.upper()
        statusValue = STATUS[status].value
    except KeyError:
        return abort(400, f'Bad request: {status} is not a valid STATUS value.')

    try:
        url = Url.get(id)
        url.status = statusValue
        url.save()
    except NotFoundError:
        error = 'Not found by url id: ' + id
        return abort(make_response(jsonify(message=error), 404))
    except ValidationError as e:
        error = 'Validation error: ' + str(e)
        logger.error(error)
        return abort(make_response(jsonify(message=error), 500))
    except Exception as e:
        error = 'Internal error: ' + str(e)
        logger.error(error)
        return abort(make_response(jsonify(message=error), 500))

@app.route('/api/shortkey/<id>/<shortKey>', methods=['POST'])
@logExecutionTime
def updateShortkeyById(id, shortKey):
    # validate for short key
    error = validateShortkey(shortKey)
    if error is not None:
        return abort(make_response(jsonify(message=error), 400))
    if isShortkeyExist(shortKey):
        error = f'Bad request: The short key "{shortKey}" is in use.'
        return abort(make_response(jsonify(message=error), 400))

    try:
        url = Url.get(id)
        url.short_key = shortKey
        url.customize = True
        url.save()
        shortUrl = SHORT_KEY_PREFIX + url.short_key
        logger.info(f'Update short key {shortKey} by id: {id}.')
        return jsonify(short_url=shortUrl, long_url=url.original_url, url_id=url.pk)
    except NotFoundError:
        error = 'Not found by url id: ' + id
        return abort(make_response(jsonify(message=error), 404))
    except ValidationError as e:
        error = 'Validation error: ' + str(e)
        logger.error(error)
        return abort(make_response(jsonify(message=error), 500))
    except Exception as e:
        error = 'Internal error: ' + str(e)
        logger.error(error)
        return abort(make_response(jsonify(message=error), 500))

@app.route('/api/urls', methods=['GET'])
def queryByUser():
    user = request.args.get('user', '')
    if len(user) == 0:
        return abort(400, f'Bad request: No user specified.')
    datas = Url.find(
        (Url.user_id == user)
    ).all()
    datas.sort(reverse=True)
    logger.info(f'User "{user}" has {len(datas)} urls')
    return build_results(datas)

def build_results(urls):
    response = []
    for url in urls:
        data = url.dict()
        data.update({'short_url': SHORT_KEY_PREFIX + data['short_key']})
        response.append(data)
    return {"results": response}

def find_by_shortkey(shortKey):
    try:
        datas = Url.find(
            (Url.short_key == shortKey)
        ).all()
    except NotFoundError:
        datas = []
    logger.info(f'Short key "{shortKey}" found {len(datas)} records')
    return datas

def create_url(short_key, long_url, expire_time, user_id, customize):
    now = datetime.datetime.utcnow().date()
    hash_value = url2hash(long_url)
    new_url = Url(original_url=long_url,
                  hash_original=hash_value,
                  short_key=short_key,
                  status=STATUS.CREATED.value,
                  create_at=now,
                  expire_time=expire_time,
                  user_id=user_id,
                  customize=customize)
    new_url.save()
    if expire_time is not None:
        delta_second = (expire_time - now).days * 24 * 3600
        logger.info(f'Set expire time {delta_second} seconds for short key {short_key}')
        new_url.expire(delta_second)
    logger.info(f'Create short url: {new_url.dict()}')
    return new_url.pk

def generate_shorturl(user_id, original_url, short_key, expire_time):
    if len(short_key) > 0:
        pk = create_url(short_key, original_url, expire_time, user_id, True)
        short_url = SHORT_KEY_PREFIX + short_key
        return short_url, pk
    
    for _ in range(SHORT_KEY_GENERATION_RETRIES_COUNT):
        short_key = generate(size=SHORT_URL_LENGTH)
        # check the short URL in use or not
        results = find_by_shortkey(short_key)
        if len(results) == 0:
            pk = create_url(short_key, original_url, expire_time, user_id, False)
            short_url = SHORT_KEY_PREFIX + short_key
            return short_url, pk

    raise Exception('Fail to generate a unique short url')

# ============= Following is Metrics Definition ============= #

@app.route('/api/service/status', methods=['GET'])
def checkServiceStatus():
    urls = Url.find().all()
    # overall
    filtered_urls = [data for data in urls if data.user_id != "lzoe"]
    redirect_urls = [data for data in filtered_urls if data.utilization > 0]
    total_number_of_urls = len(filtered_urls)
    total_number_of_redirect_urls = len(redirect_urls)
    total_redirect_times = sum(url.utilization for url in filtered_urls if url.utilization is not None)
    # users
    filtered_user_urls = [data for data in filtered_urls if data.user_id != "svc.vsan-er"]
    redirect_user_urls = [data for data in filtered_user_urls if data.utilization > 0]
    user_data = {
        "number_of_urls": len(filtered_user_urls),
        "number_of_redirected_urls": len(redirect_user_urls),
        "redirect_times": sum(url.utilization for url in filtered_user_urls if url.utilization is not None)
    }
    # bot
    filtered_bot_urls = [data for data in filtered_urls if data.user_id == "svc.vsan-er"]
    redirect_bot_urls = [data for data in filtered_bot_urls if data.utilization > 0]
    bot_data = {
        "number_of_urls": len(filtered_bot_urls),
        "number_of_redirected_urls": len(redirect_bot_urls),
        "redirect_times": sum(url.utilization for url in filtered_bot_urls if url.utilization is not None)
    }
    return jsonify(number_of_overall_urls=total_number_of_urls,
                   overall_redirect_times=total_redirect_times,
                   number_of_overall_redirected_urls=total_number_of_redirect_urls,
                   user=user_data, bot=bot_data)

@app.route('/api/url/latest/create/<days>', methods=['GET'])
def latestCreateUrl(days):
    try:
        days_ago = datetime.datetime.utcnow().date() - datetime.timedelta(days=int(days))
    except:
        return abort(make_response(jsonify(message='Bad request'), 400))
    urls = Url.find().all()
    latest_created_urls = [data for data in urls if data.create_at >= days_ago and data.user_id != "lzoe"]
    result = build_results(latest_created_urls)
    latest_created_url_result = result["results"]
    return jsonify(number_of_created_urls=len(latest_created_urls),
                   latest_created_urls=latest_created_url_result)

@app.route('/api/url/status', methods=['GET'])
def queryUrlStatus():
    urls = Url.find().all()
    filtered_urls = [data for data in urls if data.user_id != "lzoe"]
    statusCounts = Counter(url.status for url in filtered_urls)
    return jsonify(number_of_all=len(filtered_urls),
                   number_of_created_urls=statusCounts.get(STATUS.CREATED.value, 0),
                   number_of_used_urls=statusCounts.get(STATUS.USED.value, 0),
                   number_of_deactivated_urls=statusCounts.get(STATUS.DEACTIVATED.value, 0),
                   number_of_deleted_urls=statusCounts.get(STATUS.DELETED.value, 0))

def updateUrlStatus():
    now = datetime.datetime.utcnow()
    logger.info('Update url status at: {}'.format(now.strftime("%A, %d. %B %Y %I:%M:%S %p")))
    urls = Url.find().all()
    days_ago = now.date() - datetime.timedelta(days=NumOfDaysDeterminedAsDeactivated)
    days_ago_time = now - datetime.timedelta(days=NumOfDaysDeterminedAsDeactivated)
    for url in urls:
        if url.status is None:
            url.status = STATUS.USED.value if url.utilization > 0 else STATUS.CREATED.value
            url.save()
        # urls never be used and recently not be used
        if (url.status == STATUS.CREATED.value and url.create_at <= days_ago) \
           or (url.status == STATUS.USED.value and url.lastRedirectTime <= days_ago_time):
            url.status = STATUS.DEACTIVATED.value
            url.save()

scheduler = BackgroundScheduler()
scheduler.add_job(func=updateUrlStatus, trigger="cron", hour=0)
scheduler.start()

updateUrlStatus()

# Create a RedisSearch index for instances of the Url model.
Migrator().run()

logger.info(f"Connect to redis uri: {REDIS_OM_URL}")
