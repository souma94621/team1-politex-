import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { motion } from "framer-motion";

export default function Dashboard() {
  const [certId, setCertId] = useState("");
  const [result, setResult] = useState(null);

  const verifyCert = async () => {
    // mock request
    setResult({ status: "certified", valid: true });
  };

  const revokeCert = async () => {
    setResult({ status: "revoked", valid: false });
  };

  return (
    <div className="p-6 grid gap-6">
      <motion.h1
        className="text-3xl font-bold"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        Regulator Dashboard
      </motion.h1>

      <Card className="p-4">
        <CardContent className="flex flex-col gap-4">
          <Input
            placeholder="Enter Certificate ID"
            value={certId}
            onChange={(e) => setCertId(e.target.value)}
          />

          <div className="flex gap-4">
            <Button onClick={verifyCert}>Verify</Button>
            <Button onClick={revokeCert}>Revoke</Button>
          </div>
        </CardContent>
      </Card>

      {result && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card className="p-4">
            <CardContent>
              <p>Status: {result.status}</p>
              <p>Valid: {result.valid ? "Yes" : "No"}</p>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  );
}
