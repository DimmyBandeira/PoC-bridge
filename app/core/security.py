import hashlib
import time

def generate_sign(app_key: str, app_secret: str, timestamp: int) -> str:
    """
    Gera a assinatura conforme especificação iConvNet:
    sign = strtolower(md5(strtolower(md5(appKey=...&appSecret=...&time=...)) + appSecret))
    """
    # Concatenação dos parâmetros em ordem alfabética (appKey, appSecret, time)
    params_str = f"appKey={app_key}&appSecret={app_secret}&time={timestamp}"
    
    # Primeiro MD5 (em minúsculas)
    first_md5 = hashlib.md5(params_str.encode('utf-8')).hexdigest().lower()
    
    # Concatena com appSecret novamente
    second_input = first_md5 + app_secret
    
    # Segundo MD5 (em minúsculas)
    sign = hashlib.md5(second_input.encode('utf-8')).hexdigest().lower()
    
    return sign

def get_current_timestamp() -> int:
    """Retorna timestamp Unix (segundos)"""
    return int(time.time())