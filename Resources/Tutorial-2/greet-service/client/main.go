package main

import (
	"context"
	"fmt"
	"log"

	"google.golang.org/grpc"
	greetpb "github.com/Mitanshk01/Tutorial-2/Example-1/protofiles"
)

func sendRequest (client greetpb.GreetServiceClient) {	
	fmt.Println("Sending request....")

	req := &greetpb.HelloRequest{Name: "Client"}

	resp, err := client.GreetRPC(context.Background(), req)
	if err != nil {
		log.Fatalf("Error calling method")
	}
	fmt.Println("Response From Server: ", resp.GetResponse())
}

func main() {
	conn, err := grpc.Dial("localhost:50051", grpc.WithInsecure())
	if err != nil {
		log.Fatalf("Could not connect")
	}
	defer conn.Close()

	client := greetpb.NewGreetServiceClient(conn)

	sendRequest(client)
}