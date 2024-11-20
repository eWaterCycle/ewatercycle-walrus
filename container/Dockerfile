FROM r-base:4.4.2

# curl is missing in this image, have to install it manually
RUN apt -y update; apt -y install libcurl4-openssl-dev

# Install pak to install from github
RUN R -e 'install.packages("pak")'

# Install remotebmi & WALRUS & Bmi-r
RUN R -e 'pak::pak("github::ClaudiaBrauer/WALRUS")'
RUN R -e 'pak::pak("github::eWaterCycle/bmi-r")'
RUN R -e 'pak::pak("configr")'
RUN R -e 'pak::pak("github::eWaterCycle/remotebmi/R")'

# Get WALRUS BMI implementation
RUN wget https://raw.githubusercontent.com/eWaterCycle/grpc4bmi-examples/master/walrus/walrus-bmi.r
RUN mkdir /r-scripts

COPY serve_walrus.R /r-scripts/serve_walrus.R
RUN mv walrus-bmi.r /r-scripts/walrus-bmi.r

# Set BMI host so it is accessible outside the container
ENV BMI_HOST=0.0.0.0
ENV BMI_PORT=50051

EXPOSE 50051
CMD ["R", "-f", "/r-scripts/serve_walrus.R"]