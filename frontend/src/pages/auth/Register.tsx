import { useState } from 'react';
import { api } from '@/lib/axios';
import { useNavigate, Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { AlertCircle } from 'lucide-react';

export default function Register() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        if (password !== confirmPassword) {
            setError("Passwords do not match");
            return;
        }

        setLoading(true);
        setError('');
        try {
            await api.post('/auth/register', { email, password }); // Note: API current register only takes email usually, but assuming updated flow or just email for now. 
            // Checking backend routes: /register takes {email}. Password is set via confirm link.
            // Wait, V4 codex says "Usuário informa e-mail -> recebe token".
            // Let's adjust this form to just Email if that's the flow, OR stick to standard registration if backend changed.
            // Looking at auth.py: register() takes email. Token sent. 
            // So Register page should just identify itself as "Sign Up" and ask for Email.

            setSuccess(true);
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.error || 'Failed to register.');
        } finally {
            setLoading(false);
        }
    };

    if (success) {
        return (
            <div className="flex h-screen items-center justify-center bg-zinc-950 p-4">
                <Card className="w-full max-w-md border-zinc-800 bg-zinc-900 text-zinc-100">
                    <CardHeader>
                        <CardTitle className="text-green-500">Confirmation Sent</CardTitle>
                        <CardDescription className="text-zinc-400">
                            Please check your email ({email}) for a confirmation link to set your password.
                        </CardDescription>
                    </CardHeader>
                    <CardFooter>
                        <Link to="/login">
                            <Button variant="outline" className="w-full">Back to Login</Button>
                        </Link>
                    </CardFooter>
                </Card>
            </div>
        )
    }

    return (
        <div className="flex h-screen items-center justify-center bg-zinc-950 p-4">
            <Card className="w-full max-w-md border-zinc-800 bg-zinc-900 text-zinc-100">
                <CardHeader className="space-y-1">
                    <CardTitle className="text-2xl font-bold text-center">Create an Account</CardTitle>
                    <CardDescription className="text-center text-zinc-400">
                        Enter your email to get started
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleRegister} className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="email">Email</Label>
                            <Input
                                id="email"
                                type="email"
                                placeholder="m@example.com"
                                required
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="bg-zinc-950 border-zinc-800 text-white placeholder:text-zinc-500"
                            />
                        </div>

                        {/* Password hidden since flow is Email -> Confirm -> Set Password */}

                        {error && (
                            <div className="flex items-center gap-2 text-sm text-red-500 bg-red-950/30 p-2 rounded border border-red-900/50">
                                <AlertCircle className="h-4 w-4" />
                                <span>{error}</span>
                            </div>
                        )}

                        <Button type="submit" className="w-full bg-blue-600 hover:bg-blue-500 text-white" disabled={loading}>
                            {loading ? 'Sending...' : 'Sign Up'}
                        </Button>
                    </form>
                </CardContent>
                <CardFooter className="justify-center">
                    <p className="text-sm text-zinc-500">
                        Already have an account? <Link to="/login" className="text-blue-500 hover:text-blue-400">Sign In</Link>
                    </p>
                </CardFooter>
            </Card>
        </div>
    );
}
