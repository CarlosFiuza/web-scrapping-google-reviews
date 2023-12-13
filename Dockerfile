FROM public.ecr.aws/lambda/python:3.8 as stage

# Hack to install chromium dependencies
RUN yum install -y -q sudo unzip

# Find the version of latest stable build of chromium from below
# https://omahaproxy.appspot.com/
# Then follow the instructions here in below URL 
# to download old builds of Chrome/Chromium that are stable
# Current stable version of Chromium
ENV CHROMIUM_VERSION=1002910 


# Install Chromium
COPY install-browser.sh /tmp/
RUN /usr/bin/bash /tmp/install-browser.sh

FROM public.ecr.aws/lambda/python:3.8 as base

COPY chrome-deps.txt /tmp/
RUN yum install -y $(cat /tmp/chrome-deps.txt)

# Install Python dependencies for function
COPY requirements.txt /tmp/
RUN python3 -m pip install --upgrade pip -q
RUN python3 -m pip install -r /tmp/requirements.txt -q 


COPY --from=stage /opt/chrome /opt/chrome
COPY --from=stage /opt/chromedriver /opt/chromedriver
COPY src/ ${LAMBDA_TASK_ROOT}/src/

COPY .env ${LAMBDA_TASK_ROOT}

RUN ls -la

CMD ["src/selenium_etree_google.scrape_handler" ]