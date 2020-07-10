FROM maven:3.6.1
COPY . /recommendation-engine
EXPOSE 8080
RUN cd recommendation-engine && mvn package
CMD cd recommendation-engine && mvn exec:java -Dexec.mainClass="Main"