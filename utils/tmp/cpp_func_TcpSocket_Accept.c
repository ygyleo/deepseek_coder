
int Accept(char* fromIP, UINT *fromPort)
{
    assert(fromIP != NULL);    sockaddr_in from;    memset(&from, 0, sizeof(struct sockaddr_in));    from.sin_family = AF_INET;    socklen_t len = sizeof(from);    int clientSock = -1;    if ((clientSock = accept(fd_, (sockaddr*) &from, &len)) < 0 )        return clientSock;    strcpy(fromIP, inet_ntoa(from.sin_addr));    fromPort = htons(from.sin_port);    return clientSock;}
