FROM ghcr.io/ewatercycle/remotebmi-r:0.1.0

LABEL org.opencontainers.image.source="https://github.com/eWaterCycle/ewatercycle-walrus"

# Install remotebmi & WALRUS & Bmi-r
RUN R -e 'pak::pak("github::ClaudiaBrauer/WALRUS")'

# Get WALRUS BMI implementation
RUN wget https://raw.githubusercontent.com/eWaterCycle/grpc4bmi-examples/master/walrus/walrus-bmi.r
RUN mkdir /r-scripts

COPY serve_walrus.R /r-scripts/serve_walrus.R
RUN mv walrus-bmi.r /r-scripts/walrus-bmi.r

# Set BMI host so it is accessible outside the container
ENV BMI_HOST=0.0.0.0
ENV BMI_PORT=50051

EXPOSE 50051
CMD ["Rscript", "/r-scripts/serve_walrus.R"]