# Coffee Detection
Website Flask untuk klasifikasi kualitas biji kopi menggunakan model multimodal:

- gambar biji kopi
- sensor MQ-2
- sensor MQ-135
- sensor MQ-3

Output utama aplikasi adalah grade kualitas kopi, confidence model, skor aroma, dan probabilitas tiap kelas.

## 1. Masuk Ke Folder Project
Buka PowerShell, lalu jalankan:
```powershell
cd "C:\Users\HP\Downloads\coffee-detection-20260417T131300Z-3-001\coffee-detection"
```

## 2. Install Library

Jalankan:

```powershell
pip install -r requirements.txt
```

Library yang dipakai:

- Flask
- tensorflow
- numpy
- Pillow
- python-dotenv

## 3. Pastikan Model Ada

Secara default, aplikasi mencari model training di:

```text
D:\skripsi\Python\DataCoffe\cnn_multimodal_model.h5
```

Kalau model ada di lokasi lain, set `MODEL_PATH` dulu sebelum menjalankan Flask:

```powershell
$env:MODEL_PATH="D:\lokasi\model_kamu.h5"
```

## 4. Jalankan Website

Jalankan:

```powershell
flask --app app run --debug
```

Jika berhasil, terminal akan menampilkan alamat seperti:

```text
http://127.0.0.1:5000
```

Buka alamat tersebut di browser.

## 5. Cara Pakai

Di halaman website:

1. Upload foto biji kopi dengan format JPG, JPEG, atau PNG.
2. Masukkan nilai sensor:
   - MQ-135
   - MQ-2
   - MQ-3
3. Klik tombol `Jalankan Inferensi`.
4. Lihat hasil pada panel `Hasil Klasifikasi`.

## 6. Output Website

Website akan menampilkan:

- `Grade Kualitas`: hasil kelas prediksi, misalnya `Grade_A_Premium`, `Grade_B_Good`, `Grade_C_Standard`, atau `Grade_D_Defective`.
- `Skor Aroma`: skor hasil perhitungan sensor.
- `Confidence Model`: tingkat keyakinan prediksi model.
- `Probabilitas per Kelas`: persentase prediksi untuk setiap grade.
- `Perhitungan Sensor Real-Time`: detail nilai sensor dan deviasi dari referensi.

## 7. Catatan Penting

Model yang dipakai adalah model multimodal. Artinya hasil prediksi tidak hanya berdasarkan gambar, tetapi juga berdasarkan nilai sensor.

Urutan sensor yang dikirim ke model mengikuti notebook training:

```text
[mq2, mq135, mq3]
```

## 8. Troubleshooting

Jika muncul pesan:

```text
Model belum siap
```

Periksa hal berikut:

1. TensorFlow sudah terinstall:

```powershell
pip install tensorflow
```

2. File model benar-benar ada di path:

```text
D:\skripsi\Python\DataCoffe\cnn_multimodal_model.h5
```

3. Flask dijalankan dari environment Python yang sama dengan TensorFlow.

Jika website masih menampilkan hasil lama, hentikan server Flask dengan:

```text
Ctrl + C
```

Lalu jalankan ulang:

```powershell
flask --app app run --debug
```
