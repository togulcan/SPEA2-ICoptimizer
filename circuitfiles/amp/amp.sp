**aaaa
.inc 130nm.txt
.inc param.cir
m1 6  4  3 3 pfet l=lm1 w=wm1 ad=lm1*wm1 as=lm1*wm1 pd=2*(lm1+wm1) ps=2*(lm1+wm1)  
m2 7  5  3  3  pfet l=lm1 w=wm1 ad=lm1*wm1 as=lm1*wm1 pd=2*(lm1+wm1) ps=2*(lm1+wm1)  
m3 2  2  1 1 pfet l=lm2 w=wm2 ad=lm2*wm2 as=lm2*wm2 pd=2*(lm2+wm2) ps=2*(lm2+wm2)  
m4 3  2  1 1 pfet l=lm2 w=wm2 ad=lm2*wm2 as=lm2*wm2 pd=2*(lm2+wm2) ps=2*(lm2+wm2)  
m5 6  6  8 8 nfet l=lm3 w=wm3 ad=lm3*wm3 as=lm3*wm3 pd=2*(lm3+wm3) ps=2*(lm3+wm3)  
m6 7  6  8  8  nfet l=lm3 w=wm3 ad=lm3*wm3 as=lm3*wm3 pd=2*(lm3+wm3) ps=2*(lm3+wm3)  
m7 0 0 0 0 nfet l=lm3 w=wm3 ad=lm3*wm3 as=lm3*wm3 pd=2*(lm3+wm3) ps=2*(lm3+wm3)
m8 0 0 0 0 nfet l=lm3 w=wm3 ad=lm3*wm3 as=lm3*wm3 pd=2*(lm3+wm3) ps=2*(lm3+wm3)
Ib 2 8 Ib


E1 eng 0 7 0 1
L1 eng 5 1000
Cx 5 0 1000

cl 7 0 0.5e-12


Vdd 1 0 DC 1.2
Vss 0 8 DC 0

*vnin 9 0 0
vin 4 0 0.6 ac 1

.op
.PARAM AREA='2*WM1*LM1 + 2*WM2*LM2 + 2*WM3*LM3'
VX 1000 0 AREA
RX 1000 0 1K
.option fast
.option post 2
.option sim_mode = client/server
.option OPFILE=1
.op
.ac dec 100 100 10000000000
.TRAN 2n 100n 

.MEAS AC gain max PAR('db(V(7))')
.MEAS AC tmp max par('gain-3')
.MEAS AC BW when par('db(V(7))')= tmp      
.MEASURE AC hreal FIND VR(7) WHEN V(7)=1
.MEASURE AC himg  FIND VI(7) WHEN V(7)=1  
.MEAS zPOWER AVG POWER 
.MEAS zSAREA avg PAR(AREA)
.END