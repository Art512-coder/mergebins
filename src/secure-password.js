/**
 * Secure Password Hashing for Cloudflare Workers
 * Uses Web Crypto API with PBKDF2 (compatible with Cloudflare Workers environment)
 */

class SecurePasswordManager {
  constructor() {
    this.algorithm = 'PBKDF2';
    this.hash = 'SHA-256';
    this.iterations = 100000; // OWASP recommended minimum
    this.keyLength = 32; // 256 bits
  }

  /**
   * Generate a cryptographically secure salt
   */
  generateSalt() {
    const saltBuffer = crypto.getRandomValues(new Uint8Array(16));
    return Array.from(saltBuffer, byte => byte.toString(16).padStart(2, '0')).join('');
  }

  /**
   * Hash a password with PBKDF2
   * @param {string} password - Plain text password
   * @param {string} salt - Hex-encoded salt (optional, generates if not provided)
   * @returns {Promise<{hash: string, salt: string}>}
   */
  async hashPassword(password, salt = null) {
    // Generate salt if not provided
    if (!salt) {
      salt = this.generateSalt();
    }

    // Convert password to buffer
    const encoder = new TextEncoder();
    const passwordBuffer = encoder.encode(password);
    
    // Convert salt to buffer
    const saltBuffer = new Uint8Array(salt.match(/.{2}/g).map(byte => parseInt(byte, 16)));

    // Import password as key material
    const keyMaterial = await crypto.subtle.importKey(
      'raw',
      passwordBuffer,
      { name: this.algorithm },
      false,
      ['deriveBits']
    );

    // Derive key using PBKDF2
    const derivedBits = await crypto.subtle.deriveBits(
      {
        name: this.algorithm,
        salt: saltBuffer,
        iterations: this.iterations,
        hash: this.hash
      },
      keyMaterial,
      this.keyLength * 8
    );

    // Convert to hex string
    const hashArray = Array.from(new Uint8Array(derivedBits));
    const hash = hashArray.map(byte => byte.toString(16).padStart(2, '0')).join('');

    return { hash, salt };
  }

  /**
   * Verify a password against a stored hash
   * @param {string} password - Plain text password
   * @param {string} storedHash - Stored password hash
   * @param {string} salt - Salt used for hashing
   * @returns {Promise<boolean>}
   */
  async verifyPassword(password, storedHash, salt) {
    try {
      const { hash } = await this.hashPassword(password, salt);
      return hash === storedHash;
    } catch (error) {
      console.error('Password verification error:', error);
      return false;
    }
  }

  /**
   * Create a combined hash string (hash:salt format)
   * @param {string} password - Plain text password
   * @returns {Promise<string>} - Combined hash in format "hash:salt"
   */
  async createPasswordHash(password) {
    const { hash, salt } = await this.hashPassword(password);
    return `${hash}:${salt}`;
  }

  /**
   * Verify password against combined hash string
   * @param {string} password - Plain text password
   * @param {string} combinedHash - Hash in format "hash:salt"
   * @returns {Promise<boolean>}
   */
  async verifyPasswordHash(password, combinedHash) {
    try {
      const [storedHash, salt] = combinedHash.split(':');
      if (!storedHash || !salt) {
        return false;
      }
      return await this.verifyPassword(password, storedHash, salt);
    } catch (error) {
      console.error('Password hash verification error:', error);
      return false;
    }
  }
}

// Export for use in Cloudflare Workers
export { SecurePasswordManager };