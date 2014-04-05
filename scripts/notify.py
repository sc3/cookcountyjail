from aws import publish
import sys

FAIL_TOPIC = 'cookcountyjail_onFail'
SUCCESS_TOPIC = 'cookcountyjail_onSuccess'


if __name__ == '__main__':

    subject = 'DB audit: "in_jail" field set incorrectly'
    message = sys.argv[1]
    publish(FAIL_TOPIC, subject, message)