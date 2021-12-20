import requests
import logging
import pandas as pd
import time 

server_url = 'https://api.upbit.com'

def send_request(reqType, reqUrl, reqParam, reqHeader):
    try:
        err_sleep_time = 0.3
        while True:
            response = requests.request(reqType, reqUrl, params=reqParam, headers=reqHeader)

            if 'Remaining-Req' in response.headers:
                hearder_info = response.headers['Remaining-Req']
                start_idx = hearder_info.find("sec=")
                end_idx = len(hearder_info)
                remain_sec = hearder_info[int(start_idx):int(end_idx)].replace('sec=', '')

            else:
                logging.error("헤더 정보 이상")
                logging.error(response.headers)
                break

            if int(remain_sec) < 3:
                logging.debug("요청 가능회수 한도 도달! 남은횟수:" + str(remain_sec))
                time.sleep(err_sleep_time)
 
            if response.status_code == 200 or response.status_code == 201:
                break

            elif response.status_code == 429:
                logging.error("요청 가능회수 초과!:" + str(response.status_code))
                time.sleep(err_sleep_time)

            else:
                logging.error("기타 에러:" + str(response.status_code))
                logging.error(response.status_code)
                logging.error(response)
                break
 
            logging.info("[restRequest] 요청 재처리중...")
 
        return response

    except Exception:
        raise

def get_candle(target_item, tick_kind, inq_range):
    try:

        if tick_kind == "1" or tick_kind == "3" or tick_kind == "5" or tick_kind == "10" or tick_kind == "15" or tick_kind == "30" or tick_kind == "60" or tick_kind == "240":
            target_url = "minutes/" + tick_kind

        elif tick_kind == "D":
            target_url = "days"

        elif tick_kind == "W":
            target_url = "weeks"

        elif tick_kind == "M":
            target_url = "months"

        else:
            raise Exception("잘못된 틱 종류:" + str(tick_kind))
 
        logging.debug(target_url)

        querystring = {"market": target_item, "count": inq_range}
        res = send_request("GET", server_url + "/v1/candles/" + target_url, querystring, "")
        candle_data = res.json()
 
        logging.debug(candle_data)
 
        return candle_data

    except Exception:
        raise
