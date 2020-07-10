FROM maven:3.6.1
COPY . /db-updater
EXPOSE 8081
RUN cd db-updater && mvn package
CMD cd db-updater && mvn exec:java -Dexec.mainClass="Main"