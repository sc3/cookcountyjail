import boto

"""
    For documentation on Amazon's Notification Service (SNS), see: http://docs.aws.amazon.com/sns/latest/dg/welcome.html

    For the boto library's API for this service, see: https://github.com/boto/boto/blob/develop/boto/sns/connection.py.

    For more on Amazon Resource Names (ARNs), see: http://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html.

"""

AMAZON_RESOURCE_NAME = 'arn:aws:sns:us-east-1:647111127395'

def connect():
    return boto.connect_sns()

def publish(topic, subject, message, arn=AMAZON_RESOURCE_NAME):
    conn = connect()
    conn.publish(
        '{0}:{1}'.format(arn, topic),
        message, 
        subject
    )

