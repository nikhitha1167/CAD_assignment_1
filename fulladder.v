// 1-Bit Full Adder implementation using only NAND gates
module full_adder (
    input  wire a,      // Input bit A
    input  wire b,      // Input bit B
    input  wire cin,    // Carry-in bit
    output wire sum,    // Sum output
    output wire carry   // Carry-out output
);

    // Internal connecting wires for the 9 NAND gates
    wire w1, w2, w3, w4, w5, w6, w7;

    // Stage 1: Processing inputs A and B (Half Adder 1 core)
    nand g1 (w1, a, b);
    nand g2 (w2, a, w1);
    nand g3 (w3, b, w1);
    nand g4 (w4, w2, w3); // w4 represents (A ^ B)

    // Stage 2: Processing Intermediate Sum (w4) and Carry-In (cin)
    nand g5 (w5, w4, cin);
    nand g6 (w6, w4, w5);
    nand g7 (w7, cin, w5);
    
    // Stage 3: Final Outputs
    nand g8 (sum, w6, w7);     // Generates the final Sum
    nand g9 (carry, w5, w1);   // Generates the final Carry-out

endmodule