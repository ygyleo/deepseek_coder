
ssize_t read_n(void* msg, size_t buf_len)
{
    assert(msg != NULL);    ssize_t recv_size = 0;    ssize_t a_recv_size;    while ((a_recv_size = ::read(fd_, (char*) msg + recv_size, buf_len - recv_size)) > 0) {        recv_size += a_recv_size;        if ( recv_size == buf_len )            break;    }    return recv_size;}
