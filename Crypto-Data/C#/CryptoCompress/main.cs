using System;
using System.IO;
using System.IO.Compression;
using System.Security.Cryptography;

class Program
{
    public static void Main(string[] args)
    {
        string filePath = "myfile.txt";
        byte[] key = GenerateRandomKey(32);
        byte[] iv = GenerateRandomKey(16);
        CompressAndEncryptFile(filePath, key, iv);
        Console.WriteLine("The file has been compressed and encrypted successfully.");
    }

    static byte[] GenerateRandomKey(int size)
    {
        byte[] key = new byte[size];
        RandomNumberGenerator.Fill(key);
        return key;
    }

    static void CompressAndEncryptFile(string inFile, byte[] key, byte[] iv)
    {
        string outFile = "encrypted_" + Path.GetFileName(inFile) + ".dat";
        using (FileStream originalFileStream = new FileStream(inFile, FileMode.Open))
        using (FileStream encryptedCompressedFileStream = File.Create(outFile))
        using (Aes aes = Aes.Create())
        {
            aes.Key = key;
            aes.IV = iv;
            using (CryptoStream cryptoStream = new CryptoStream(encryptedCompressedFileStream, aes.CreateEncryptor(), CryptoStreamMode.Write))
            using (GZipStream compressionStream = new GZipStream(cryptoStream, CompressionMode.Compress))
            {
                originalFileStream.CopyTo(compressionStream);
            }
        }
    }
}