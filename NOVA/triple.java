public class drive {
    public static void main(String[] args) {
        Thread t1 = new Thread(() -> {
            System.out.println("Hello from thread 1");
        });

        Thread t2 = new Thread(() -> {
            System.out.println("Hello from thread 2");
        });


        t1.start();
        t2.start();
    }
}