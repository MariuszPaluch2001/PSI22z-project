#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>

int work() { return 1; }
#define BUFSIZE 64
#define FIRST_BYTE_MASK 0xFF
int main() {
	int sfd; 
	struct sockaddr_in servaddr, clientaddr;
	long temp_addr;
	char buf[BUFSIZE];
	int length;

	sfd = socket(AF_INET, SOCK_DGRAM, 0);
	if (sfd < 0) {
		perror("Problem with creating a socket");
		exit(1);
	}
	servaddr.sin_family = AF_INET;
	servaddr.sin_addr.s_addr = INADDR_ANY;
	servaddr.sin_port = 0;

	if (bind(sfd, (struct sockadrr *)&servaddr, sizeof(servaddr)) != 0) {
		perror("Problem with binding address");
		exit(1);
	}
	length = sizeof(servaddr);
	if (getsockname(sfd, (struct sockaddr *) &servaddr, &length) < 0) {
		perror("Problem with accessing received port");
		exit(1);
	}
	printf("Received port: %u\n", ntohs(servaddr.sin_port));

	while (work()) {
		memset(buf, 0, BUFSIZE * sizeof(buf[0]));
		if (recvfrom(sfd, buf, BUFSIZE, 0,  &clientaddr, &length) < 0) {
			perror("Problem with receiving data");
			exit(1);
		}
		temp_addr = ntohl(clientaddr.sin_addr.s_addr);
		printf("Received data from address: %lu.%lu.%lu.%lu\n",
			(temp_addr>>24) & FIRST_BYTE_MASK,
			(temp_addr>>16) & FIRST_BYTE_MASK,
			(temp_addr>>8) & FIRST_BYTE_MASK,
			(temp_addr>>0) & FIRST_BYTE_MASK);
		buf[BUFSIZE - 1] = 0;
		printf("%s", buf);

	}

	if (close(sfd) != 0) {
		perror("Problem with closing socket");
		exit(1);
	}

	return 0;
}
