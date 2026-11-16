CC ?= cc
CFLAGS = -std=c11 -Wall -Wextra -Werror -I../../include
SRC = ../../src/health_core.c ../../src/supervisor_core.c test_main.c

test: test_main
	./test_main

test_main: $(SRC)
	$(CC) $(CFLAGS) -o $@ $(SRC)

clean:
	rm -f test_main
