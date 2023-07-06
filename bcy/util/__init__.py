import re
from faker import Faker


def create_headers() -> dict:
    """
    生成随机headers
    

    :return:
    """
    fake = Faker()
    headers = {
        'User-Agent': fake.user_agent(),
        'Cookie': 's_v_web_id=verify_lhla8qax_qv0XDpSt_6c5T_4RNI_8FRS_ikhU9vgr8XPF; PHPSESSID=e7223f726d40595079a6ec503ca2f381; lang_set=zh; mobile_set=no; tt_webid=7244469692798617147; passport_csrf_token=427912a08ed67136fb332cbb87b32cd3; passport_csrf_token_default=427912a08ed67136fb332cbb87b32cd3; n_mh=xBxt1yGax1skamK38AC5flfwTEauWJGrAUrO5aZiQy4; passport_auth_status=4df0c65f528617df5562b4598a84bc68%2C; passport_auth_status_ss=4df0c65f528617df5562b4598a84bc68%2C; sid_guard=ecdbf2721dc489518a4e2154bb8ded3b%7C1686734811%7C5184000%7CSun%2C+13-Aug-2023+09%3A26%3A51+GMT; uid_tt=b2d30bf7cbdb2cd76796a17e940366ea; uid_tt_ss=b2d30bf7cbdb2cd76796a17e940366ea; sid_tt=ecdbf2721dc489518a4e2154bb8ded3b; sessionid=ecdbf2721dc489518a4e2154bb8ded3b; sessionid_ss=ecdbf2721dc489518a4e2154bb8ded3b; sid_ucp_v1=1.0.0-KGI0OTRlMGM4OGU2ZmZkM2JmOTFhMzRkZjhjM2JhMjMxODQ4MDMyNTUKFwjb6tCXqfTbARDbj6akBhiZCjgCQPEHGgJsZiIgZWNkYmYyNzIxZGM0ODk1MThhNGUyMTU0YmI4ZGVkM2I; ssid_ucp_v1=1.0.0-KGI0OTRlMGM4OGU2ZmZkM2JmOTFhMzRkZjhjM2JhMjMxODQ4MDMyNTUKFwjb6tCXqfTbARDbj6akBhiZCjgCQPEHGgJsZiIgZWNkYmYyNzIxZGM0ODk1MThhNGUyMTU0YmI4ZGVkM2I; store-region=cn-he; store-region-src=uid; _csrf_token=946e286a066128621476ed06c373afa7; _bcy_user_id=U2FsdGVkX19g6n78NVymq0Ih0hk5tGStxdo+ITWaPM4DBCwLC96oiDDIXg/Eu3h/cK2PyynnFJcgVpDBAPhMJWYW4TPTlW1wuaS11Ji137c=; tt_scid=lF40.w1F3SPhlUyITcX75M7xq.coePDLC1JQX.H4uYzgeQHR74q6u6w5AWg5sGBm7342; msToken=BPw9JRB7sguBw8Cznzk1NhGoP1WZoBCjyl0dN3A9gmh_vR0eMXA9I252xyMmaL-n_a7nlHkU1tJSv0vDbTDWwiJbbqea8DD63GlkWSQlYBiAJiGGdj7s'
    }
    return headers

def get_file_name(img_url:str) -> str:
    """生成文件名
    
    - Returns:
        - str: file name
    """
    reg = 'banciyuan/(.*)\.image'
    matched:str = re.findall(reg,img_url)[0]
    matched = matched.replace('~','_').replace(':','_')
    return matched