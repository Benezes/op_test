const {
  S3Client,
  GetObjectCommand,
  HeadObjectCommand,
} = require("@aws-sdk/client-s3");
const {
  DynamoDBClient,
  UpdateItemCommand,
} = require("@aws-sdk/client-dynamodb");
const pdf = require("pdf-parse");

const s3 = new S3Client();
const dynamodb = new DynamoDBClient();

const TABLE_NAME = process.env.DYNAMODB_TABLE || "FileMetadata";

exports.handler = async (event) => {
  const record = event.Records[0];
  const bucket = record.s3.bucket.name;
  const key = decodeURIComponent(record.s3.object.key.replace(/\+/g, " "));

  const headResponse = await s3.send(
    new HeadObjectCommand({ Bucket: bucket, Key: key })
  );
  const contentType = headResponse.ContentType;
  const fileSize = headResponse.ContentLength;

  let pageCount = null;
  let extractedText = "";

  if (contentType === "application/pdf") {
    const getResponse = await s3.send(
      new GetObjectCommand({ Bucket: bucket, Key: key })
    );
    const chunks = [];
    for await (const chunk of getResponse.Body) {
      chunks.push(chunk);
    }
    const buffer = Buffer.concat(chunks);
    const pdfData = await pdf(buffer);
    pageCount = pdfData.numpages;
    extractedText = pdfData.text.substring(0, 10000);
  }

  const fileId = key.split("/").pop().split(".")[0];

  await dynamodb.send(
    new UpdateItemCommand({
      TableName: TABLE_NAME,
      Key: { file_id: { S: fileId } },
      UpdateExpression:
        "SET file_size = :size, page_count = :pages, extracted_text = :text, lambda_processed = :processed, s3_key = :key",
      ExpressionAttributeValues: {
        ":size": { N: String(fileSize) },
        ":pages": pageCount ? { N: String(pageCount) } : { NULL: true },
        ":text": { S: extractedText },
        ":processed": { BOOL: true },
        ":key": { S: key },
      },
    })
  );

  return { statusCode: 200, body: "Processed" };
};
