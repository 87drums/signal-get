unsigned long bt = micros(); //bt = before time

void setup() {
  Serial.begin(57600);//レート選択 115200 57600 38400
}
int i = 0;
void loop() {
  /*//delayMicroseconds(500);
  int input = Serial.read();
  Serial.println(input);
  if(input == 111){
    int a0 = analogRead(0); //analog0から読み込み
    int a1 = analogRead(1); //analog1から読み込み
    int t = micros() - bt;
    bt += t;
  
    //計測データ2バイト分
    int out1_0 = a0 >> 8; //上位8桁
    int out1_1 = a0 & 255; //下位8桁
  
    int out2_0 = a1 >> 8; //上位8桁
    int out2_1 = a1 & 255; //下位8桁
    
    int t1 = t >> 8;
    int t2 = t & 255;
  
    //タイムスタンプ2バイト分
  
    //Serial.write(111);
    Serial.write(out1_0);
    Serial.write(out1_1);
    Serial.write(out2_0);
    Serial.write(out2_1);
  
    Serial.write(t1);
    Serial.write(t2);
  }*/
  //delayMicroseconds(680);
  
  int a0 = analogRead(0); //analog0から読み込み
  int a1 = analogRead(1); //analog1から読み込み
  int t = micros() - bt;
  bt += t;

  //計測データ2バイト分
  int out1_0 = a0 >> 8; //上位8桁
  int out1_1 = a0 & 255; //下位8桁

  int out2_0 = a1 >> 8; //上位8桁
  int out2_1 = a1 & 255; //下位8桁
  
  int t1 = t >> 8;
  int t2 = t & 255;

  //タイムスタンプ2バイト分

  Serial.write(i);
  if(i >= 250)i = 0;
  else i++;

  Serial.write(out1_0);
  Serial.write(out1_1);
  Serial.write(out2_0);
  Serial.write(out2_1);

  Serial.write(t1);
  Serial.write(t2);
}
