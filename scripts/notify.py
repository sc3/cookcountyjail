from aws import publish
import sys

FAIL_TOPIC = 'cookcountyjail_onFail'
SUCCESS_TOPIC = 'cookcountyjail_onSuccess'


if __name__ == '__main__':

    subject = 'DB Audit Failed'
    message = sys.stdin.read()
    publish(FAIL_TOPIC, subject, message)
