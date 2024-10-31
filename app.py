from flask import Flask, request, redirect, jsonify, abort, render_template, make_response

import functools
import time
from nanoid import generate

from redis_om import Migrator
from redis_om.model import NotFoundError
from pydantic import ValidationError

from src.schema import Url
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

@app.route('/api/service/status', methods=['GET'])
def checkServiceStatus():
    urls = Url.find().all()
    # overall
    filtered_urls = [data for data in urls if data.user_id != "lzoe"]
    total_number_of_urls = len(filtered_urls)
    total_redirect_times = sum(url.utilization for url in filtered_urls if url.utilization is not None)
    # user's url
    filtered_user_urls = [data for data in filtered_urls if data.user_id != "svc.vsan-er"]
    number_of_user_urls = len(filtered_user_urls)
    number_of_bot_urls = total_number_of_urls - number_of_user_urls
    # url which redirect time is 0
    not_redirect_urls = [data for data in filtered_urls if data.utilization == 0]
    number_of_not_redirect_urls = len(not_redirect_urls)
    return jsonify(number_of_overall_urls=total_number_of_urls,
                   overall_redirect_times=total_redirect_times,
                   number_of_user_urls=number_of_user_urls,
                   number_of_bot_urls=number_of_bot_urls,
                   number_of_not_redirect_urls=number_of_not_redirect_urls)

@app.route('/api/url/deprecated/analyze/<days>', methods=['GET'])
def analyzeUrl(days):
    try:
        days_ago = datetime.datetime.utcnow().date() - datetime.timedelta(days=int(days))
        days_ago_time = datetime.datetime.utcnow() - datetime.timedelta(days=int(days))
    except:
        return abort(make_response(jsonify(message='Bad request'), 400))
    logger.info(f'Analyze {days_ago} ago the urls redirect times and last redirect time.')
    urls = Url.find().all()
    unused_urls = [data for data in urls if data.utilization == 0 and data.create_at <= days_ago]
    recently_unused_urls = [data for data in urls if data.utilization > 0 and data.lastRedirectTime != None and data.lastRedirectTime <= days_ago_time]
    
    result = build_results(unused_urls)
    unused_url_result = result["results"]
    
    result = build_results(recently_unused_urls)
    recently_unused_url_result = result["results"]
    
    return jsonify(number_of_unused_urls=len(unused_urls), unused_urls=unused_url_result,
                   number_of_recently_unused_urls=len(recently_unused_urls),
                   recently_unused_urls=recently_unused_url_result)

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
    url.save()
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
        result.update({'short_url': SHORT_KEY_PREFIX + result['short_key']})
        return result
    except NotFoundError:
        error = 'Not found by url id: ' + id
        return abort(make_response(jsonify(message=error), 404))

@app.route('/api/url/<id>', methods=['DELETE'])
def deleteById(id):
    try:
        ret = Url.delete(id)
        # Delete returns 1 if the url existed and was deleted, or 0 if they didn't exist.
        return jsonify('ok')
    except NotFoundError:
        error = 'Not found by url id: ' + id
        return abort(make_response(jsonify(message=error), 404))

@app.route('/api/url/<id>', methods=['POST'])
def updateById(id):
    try:
        url = Url.get(id)
    except NotFoundError:
        error = 'Not found by url id: ' + id
        return abort(make_response(jsonify(message=error), 404))

    try:
        data = json.loads(request.data.decode())
        originalUrl = data['original_url']
        validateUrl(originalUrl)
    except Exception as e:
        error = f'Bad request: {e}'
        return abort(make_response(jsonify(message=error), 400))
    
    try:
        url.original_url = originalUrl
        url.hash_original = url2hash(originalUrl)
        url.save()
        shortUrl = SHORT_KEY_PREFIX + url.short_key
        return jsonify(short_url=shortUrl, long_url=url.original_url, url_id=url.pk)
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
    except:
        return abort(make_response(jsonify(message='Bad request'), 400))

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

    try:
        url = urls[0]
        logger.debug(url)
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
        logger.debug(url)
        url.short_key = shortKey
        url.save()
        shortUrl = SHORT_KEY_PREFIX + url.short_key
        return jsonify(short_url=shortUrl, long_url=url.original_url, url_id=url.pk)
    except ValidationError as e:
        error = 'Validation error: ' + str(e)
        logger.error(error)
        return abort(make_response(jsonify(message=error), 500))
    except NotFoundError:
        error = 'Not found by url id: ' + id
        return abort(make_response(jsonify(message=error), 404))

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

def create_url(short_key, long_url, expire_time, user_id):
    now = datetime.datetime.utcnow().date()
    hash_value = url2hash(long_url)
    new_url = Url(original_url=long_url, hash_original=hash_value, short_key=short_key, 
                  expire_time=expire_time, create_at=now, user_id=user_id)
    new_url.save()
    if expire_time is not None:
        delta_second = (expire_time - now).days * 24 * 3600
        logger.info(f'Set expire time {delta_second} seconds for short key {short_key}')
        new_url.expire(delta_second)
    logger.info(f'Create short url: {new_url.dict()}')
    return new_url.pk

def generate_shorturl(user_id, original_url, short_key, expire_time):
    if len(short_key) > 0:
        pk = create_url(short_key, original_url, expire_time, user_id)
        short_url = SHORT_KEY_PREFIX + short_key
        return short_url, pk
    
    for _ in range(SHORT_KEY_GENERATION_RETRIES_COUNT):
        short_key = generate(size=SHORT_URL_LENGTH)
        # check the short URL in use or not
        results = find_by_shortkey(short_key)
        if len(results) == 0:
            pk = create_url(short_key, original_url, expire_time, user_id)
            short_url = SHORT_KEY_PREFIX + short_key
            return short_url, pk

    raise Exception('Fail to generate a unique short url')

# Create a RedisSearch index for instances of the Url model.
Migrator().run()

logger.info(f"Connect to redis uri: {REDIS_OM_URL}")
