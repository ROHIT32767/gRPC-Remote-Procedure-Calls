package main

import (
	"context"
	"fmt"
	"log"
	"net"

	"google.golang.org/grpc"
	greetpb "github.com/Mitanshk01/Tutorial-2/Example-1/protofiles"
)

type server struct {
	greetpb.UnimplementedGreetServiceServer
}

func (s *server) GreetRPC (ctx context.Context, req *greetpb.HelloRequest) (*greetpb.HelloResponse, error) {
	name := req.GetName()
	response := fmt.Sprintf("Hello %s, welcome to gRPC", name)
	return &greetpb.HelloResponse{Response: response}, nil
}

func main () {
	listener, err := net.Listen("tcp", ":50051")

	if(err != nil) {
		log.Fatalf("Failed to listen")
	}

	grpcServer := grpc.NewServer()
	greetpb.RegisterGreetServiceServer(grpcServer, &server{})

	log.Println("gRPC server is running")

	if err := grpcServer.Serve(listener); err != nil {
		log.Fatalf("Failed to serve")
	}
}