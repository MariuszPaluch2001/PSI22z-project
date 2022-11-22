#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <stdio.h>
#include <sys/types.h>

#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>

#define BUFF_LEN 64
#define SEND_COUNT 10

struct data_struct
{
	long int a;
	short int b;
	char c[10];
};

int main(int argc, char *argv[])
{

	struct data_struct data;
	memset(&data, 0, sizeof(data));
	data.a = 100;
	data.b = 100;
	strcpy(data.c, "test");
	if (argc != 3)
	{
		perror("Incorect number of arguments.\n");
		exit(1);
	}

	char serv_addr[BUFF_LEN];
	strcpy(serv_addr, argv[1]);

	int sock;
	int port = atoi(argv[2]);

	struct sockaddr_in si_serv;
	struct hostent *hp;

	sock = socket(AF_INET, SOCK_DGRAM, 0);
	if (sock == -1)
	{
		perror("opening stream socket");
		exit(1);
	}

	si_serv.sin_family = AF_INET;
	si_serv.sin_port = htons(port);

	if (inet_aton(serv_addr, &si_serv.sin_addr) == 0)
	{
		perror("inet_aton() failed\n");
		exit(1);
	}
	for (int i = 0; i < SEND_COUNT; i++)
	{
		if (sendto(sock, &data, sizeof(data), 0,
							 (struct sockaddr *)&si_serv, sizeof(si_serv)) == -1)
			perror("Sending datagram message failed.\n");
	}
	close(sock);
	exit(0);
	return 0;
}
